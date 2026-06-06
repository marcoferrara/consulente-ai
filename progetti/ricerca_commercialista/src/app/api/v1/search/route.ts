import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { Prisma } from "@prisma/client";
import { searchWithNlp } from "@/lib/nlpEngine";
import { generateGroundedSummary } from "@/lib/claudeCitations";

export async function GET(req: NextRequest) {
  const startTime = Date.now();
  const searchParams = req.nextUrl.searchParams;
  const q = searchParams.get("q") || "";
  const erp = searchParams.get("erp") || "";
  const grounded = searchParams.get("grounded") === "true";

  try {
    // 1. Get the default user for audit logging (idempotent fallback if seed wasn't run)
    let defaultUser = await prisma.user.findFirst();
    if (!defaultUser) {
      const firm = await prisma.firm.upsert({
        where: { vatNumber: "99999999999" },
        update: {},
        create: { name: "Studio Demo", vatNumber: "99999999999" },
      });
      defaultUser = await prisma.user.upsert({
        where: { email: "demo@studiodemo.it" },
        update: {},
        create: {
          name: "Accountant Demo",
          email: "demo@studiodemo.it",
          passwordHash: "demo1234",
          firmId: firm.id,
        },
      });
    }

    // 2. Build database pre-query conditions (filter by ERP gestionale if requested)
    const whereCondition: Prisma.AccountingProcedureWhereInput = {};

    if (erp) {
      whereCondition.erpMappings = {
        some: {
          erpName: { contains: erp },
        },
      };
    }

    // 3. Query all candidate procedures including their ERP guides
    const procedures = await prisma.accountingProcedure.findMany({
      where: whereCondition,
      include: {
        erpMappings: true,
      },
    });

    // 4. Feed candidate records into the custom NLP search and intent parser
    const nlpResult = searchWithNlp(procedures, q);
    const rankedProcedures = nlpResult.scoredProcedures.map((sp) => sp.procedure);
    const detectedIntent = nlpResult.detectedIntent;

    // 5. Se grounded=true, arricchisce la prima procedura con Citations API
    type GroundedData = { summary: string; citations: unknown[] };
    let groundedData: GroundedData | null = null;

    if (grounded && rankedProcedures.length > 0) {
      const topProcedure = rankedProcedures[0] as typeof rankedProcedures[0] & {
        sourceContents?: { source_name: string; url: string; content: string }[];
      };
      const sourceContents = topProcedure.sourceContents;



      if (Array.isArray(sourceContents) && sourceContents.length > 0) {
        try {
          const result = await generateGroundedSummary(topProcedure.title, sourceContents);
          groundedData = result;
        } catch (e) {
          console.error("Citations API error:", e);
          // Fallback silenzioso: si usa normativeSummary statico
        }
      }
    }

    const executionTimeMs = Date.now() - startTime;

    // 6. Fire-and-forget audit log — don't block the response
    const matchedIds = rankedProcedures.map((p) => p.id).join(", ");
    void prisma.searchLog.create({
      data: {
        userId: defaultUser.id,
        query: q || "[Tutte le procedure]",
        erpFilter: erp || null,
        searchIntent: detectedIntent,
        matchedProceduresCount: rankedProcedures.length,
        responseGiven: matchedIds || "Nessun risultato",
        executionTimeMs,
      },
    }).catch((e) => console.error("Audit log error:", e));

    return NextResponse.json(
      {
        success: true,
        query: q,
        erpFilter: erp,
        grounded,
        executionTimeMs,
        detectedIntent,
        count: rankedProcedures.length,
        data: rankedProcedures,
        ...(groundedData && { groundedResult: groundedData }),
      },
      { status: 200 }
    );
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Internal Server Error";
    console.error("Search API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: errorMessage,
      },
      { status: 500 }
    );
  }
}
