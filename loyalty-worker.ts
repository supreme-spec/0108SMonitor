import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const BATCH_SIZE = 20;
const WORKER_INTERVAL_MS = 3000;

let _broadcast: ((data: any) => void) | null = null;

export function setBroadcastFn(fn: (data: any) => void) {
  _broadcast = fn;
}

function calculateScore(visits: any[]): number {
  if (!visits || visits.length < 2) return 0;

  const intervals: number[] = [];
  for (let i = 0; i < visits.length - 1; i++) {
    const diff = (new Date(visits[i].visit_date).getTime() - new Date(visits[i + 1].visit_date).getTime()) / (1000 * 60 * 60 * 24);
    if (diff > 0) intervals.push(diff);
  }

  let score = 0;
  if (intervals.length > 0) {
    const avgInterval = intervals.reduce((s, v) => s + v, 0) / intervals.length;
    if (avgInterval <= 1) score = 100;
    else if (avgInterval <= 3) score = 90 - (avgInterval - 1) * 2.5;
    else if (avgInterval <= 7) score = 85 - (avgInterval - 3) * 5;
    else if (avgInterval <= 14) score = 65 - (avgInterval - 7) * 3;
    else if (avgInterval <= 30) score = 45 - (avgInterval - 14) * 0.8;
    else if (avgInterval <= 60) score = 25 - (avgInterval - 30) * 0.3;
    else score = 10;
  }

  const visitBonus = Math.min(15, visits.length * 1.5);
  return Math.min(100, Math.round(score + visitBonus));
}

export async function runLoyaltyWorkerTick() {
  try {
    const dirtyPersons = await prisma.person.findMany({
      where: { needsLoyaltyUpdate: true },
      take: BATCH_SIZE,
      select: { id: true },
    });

    if (dirtyPersons.length === 0) return;

    for (const p of dirtyPersons) {
      const visits = await prisma.personVisit.findMany({
        where: { person_id: p.id },
        orderBy: { visit_date: 'desc' },
        take: 20,
      });

      const newIndex = calculateScore(visits);

      await prisma.person.update({
        where: { id: p.id },
        data: {
          loyaltyIndex: newIndex,
          needsLoyaltyUpdate: false,
        },
      });

      if (typeof _broadcast === 'function') {
        _broadcast({
          type: 'LOYALTY_UPDATED',
          personId: p.id,
          loyaltyIndex: newIndex,
          timestamp: Date.now(),
        });
      }
    }
  } catch (err) {
    console.error('[LoyaltyWorker] Tick error:', err);
  }
}

export function startLoyaltyWorker() {
  console.log(`[LoyaltyWorker] Started (Interval: ${WORKER_INTERVAL_MS}ms, Batch: ${BATCH_SIZE})`);
  runLoyaltyWorkerTick();
  setInterval(runLoyaltyWorkerTick, WORKER_INTERVAL_MS);
}
