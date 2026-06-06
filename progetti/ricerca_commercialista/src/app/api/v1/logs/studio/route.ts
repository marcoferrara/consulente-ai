import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    // 1. Fetch recent search logs with user details
    const logs = await prisma.searchLog.findMany({
      orderBy: {
        createdAt: "desc",
      },
      include: {
        user: {
          select: {
            name: true,
            email: true,
            role: true,
          },
        },
      },
      take: 50, // Limit to recent 50 logs
    });

    // 2. Aggregate analytics statistics for the administrator panel
    const totalSearches = await prisma.searchLog.count();
    const averageTimeResult = await prisma.searchLog.aggregate({
      _avg: {
        executionTimeMs: true,
      },
    });

    const averageExecutionTime = Math.round(averageTimeResult._avg.executionTimeMs || 0);

    // Group searches by ERP using aggregation instead of loading all records
    const erpGroups = await prisma.searchLog.groupBy({
      by: ["erpFilter"],
      where: { erpFilter: { not: null } },
      _count: { erpFilter: true },
    });

    const erpDistribution: Record<string, number> = {};
    erpGroups.forEach((group) => {
      if (group.erpFilter) {
        erpDistribution[group.erpFilter] = group._count.erpFilter;
      }
    });

    return NextResponse.json(
      {
        success: true,
        data: {
          logs,
          stats: {
            totalSearches,
            averageExecutionTimeMs: averageExecutionTime,
            erpDistribution,
          },
        },
      },
      { status: 200 }
    );
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Internal Server Error";
    console.error("Logs Studio API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: errorMessage,
      },
      { status: 500 }
    );
  }
}
