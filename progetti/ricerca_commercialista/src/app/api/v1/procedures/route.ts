import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

interface ErpMappingInput {
  erpName: string;
  stepByStepGuide: string[];
  notes?: string | null;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { title, normativeSummary, electronicInvoicingFields, officialSources, erpMappings } = body;

    // Validation
    if (!title || !normativeSummary || !electronicInvoicingFields || !officialSources) {
      return NextResponse.json(
        {
          success: false,
          error: "Missing required fields: title, normativeSummary, electronicInvoicingFields, officialSources are all required.",
        },
        { status: 400 }
      );
    }

    // Atomic transaction to create both procedure and mappings
    const newProcedure = await prisma.$transaction(async (tx) => {
      const procedure = await tx.accountingProcedure.create({
        data: {
          title,
          normativeSummary,
          electronicInvoicingFields: electronicInvoicingFields,
          officialSources: officialSources,
        },
      });

      if (erpMappings && Array.isArray(erpMappings) && erpMappings.length > 0) {
        await tx.erpMapping.createMany({
          data: erpMappings.map((mapping: ErpMappingInput) => ({
            procedureId: procedure.id,
            erpName: mapping.erpName,
            stepByStepGuide: mapping.stepByStepGuide,
            notes: mapping.notes || null,
          })),
        });
      }

      // Fetch the fully created procedure with its mappings to return
      return await tx.accountingProcedure.findUnique({
        where: { id: procedure.id },
        include: { erpMappings: true },
      });
    });

    return NextResponse.json(
      {
        success: true,
        message: "Accounting procedure created successfully.",
        data: newProcedure,
      },
      { status: 201 }
    );
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Internal Server Error";
    console.error("Procedures creation API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: errorMessage,
      },
      { status: 500 }
    );
  }
}
