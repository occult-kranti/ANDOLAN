import { describe, expect, it } from 'vitest';
import { CAMPAIGN, EVIDENCE, chooseEnding, getStageDialogue, getChoiceConsequence, getDocumentStatus, type CampaignMetrics, type StoryDecision } from '../packages/content/src/index';
import { WORLD, isBlocked } from '../packages/sim/src/world';

const clamp = (value: number) => Math.max(0, Math.min(100, value));
const apply = (metrics: CampaignMetrics, effects: Partial<CampaignMetrics> = {}): CampaignMetrics => ({
  trust: clamp(metrics.trust + (effects.trust ?? 0)),
  care: clamp(metrics.care + (effects.care ?? 0)),
  accountability: clamp(metrics.accountability + (effects.accountability ?? 0)),
});

describe('authored campaign integrity', () => {
  it('uses existing reachable landmarks and stable unique identifiers', () => {
    const ids = new Set<string>();
    for (const chapter of CAMPAIGN) {
      expect(ids.has(chapter.id)).toBe(false);
      ids.add(chapter.id);
      expect(chapter.stages.length).toBeGreaterThanOrEqual(3);
      const stageIds = new Set<string>();
      for (const stage of chapter.stages) {
        expect(stageIds.has(stage.id)).toBe(false);
        stageIds.add(stage.id);
        const target = WORLD.landmarks.find(point => point.id === stage.targetId);
        expect(target, `${chapter.id}/${stage.id} has a real target`).toBeDefined();
        expect(isBlocked(target!.x, target!.z), `${stage.targetId} is accessible`).toBe(false);
        if (stage.trigger === 'arrive') expect(stage.objective).toContain(target!.name);
        expect(stage.objective.length).toBeLessThan(160);
        expect(stage.dialogue.length).toBeGreaterThan(0);
        for (const line of stage.dialogue) {
          expect(line.speaker.length).toBeGreaterThan(0);
          expect(line.text.length).toBeGreaterThan(0);
          expect(line.text.length).toBeLessThan(300);
        }
      }
    }
  });

  it('resolves every evidence reference and distinguishes claim limits', () => {
    const references = CAMPAIGN.flatMap(chapter => chapter.stages.flatMap(stage => [
      ...(stage.evidence ?? []), ...(stage.documents ?? []), ...(stage.choices ?? []).flatMap(choice => choice.evidence ?? []),
    ]));
    for (const id of references) {
      expect(EVIDENCE[id], `missing evidence ${id}`).toBeDefined();
      expect(EVIDENCE[id]!.id).toBe(id);
      expect(EVIDENCE[id]!.qualification.length).toBeGreaterThan(30);
      expect(EVIDENCE[id]!.source.length).toBeGreaterThan(10);
    }
    expect(new Set(references).size).toBe(Object.keys(EVIDENCE).length);
  });

  it('defines only bounded declarative choices with distinct consequences', () => {
    for (const chapter of CAMPAIGN) for (const stage of chapter.stages) {
      if (stage.trigger === 'choice') {
        expect(stage.choices?.length).toBe(3);
        expect(new Set(stage.choices!.map(choice => choice.id)).size).toBe(3);
        expect(new Set(stage.choices!.map(choice => JSON.stringify(choice.effects))).size).toBe(3);
        for (const choice of stage.choices!) {
          expect(getChoiceConsequence({ chapterId: chapter.id, stageId: stage.id, choiceId: choice.id }).length).toBeGreaterThan(30);
          for (const [metric, delta] of Object.entries(choice.effects ?? {})) {
            expect(['trust', 'care', 'accountability']).toContain(metric);
            expect(Number.isFinite(delta)).toBe(true);
            expect(Math.abs(delta)).toBeLessThanOrEqual(30);
          }
        }
      } else {
        expect(stage.choices).toBeUndefined();
      }
    }
    // A saved content payload can be serialized without executable scripts or circular state.
    expect(JSON.parse(JSON.stringify(CAMPAIGN))).toEqual(CAMPAIGN);
  });

  it('keeps travel and in-world interaction in every chapter', () => {
    for (const chapter of CAMPAIGN) {
      expect(new Set(chapter.stages.map(stage => stage.targetId)).size).toBeGreaterThanOrEqual(2);
      expect(chapter.stages.some(stage => stage.trigger === 'interact' || stage.trigger === 'choice')).toBe(true);
    }
    expect(CAMPAIGN[0]!.stages.some(stage => stage.trigger === 'enter_vehicle')).toBe(true);
  });

  it('places callbacks after their real decisions and resolves them from saved history', () => {
    const ordered = CAMPAIGN.flatMap(chapter => chapter.stages.map(stage => ({ chapter, stage })));
    for (const [index, { stage }] of ordered.entries()) {
      expect(getStageDialogue(stage, [])).toEqual(stage.dialogue);
      for (const variant of stage.dialogueVariants ?? []) {
        const earlier = ordered.findIndex(item => item.chapter.id === variant.when.chapterId && item.stage.id === variant.when.stageId);
        expect(earlier).toBeGreaterThanOrEqual(0);
        expect(earlier).toBeLessThan(index);
        expect(ordered[earlier]!.stage.choices?.some(choice => choice.id === variant.when.choiceId)).toBe(true);
        const restoredHistory = JSON.parse(JSON.stringify([variant.when])) as StoryDecision[];
        expect(getStageDialogue(stage, restoredHistory)).toEqual(variant.dialogue);
        expect(variant.dialogue).not.toEqual(stage.dialogue);
        for (const line of variant.dialogue) expect(line.text.length).toBeLessThan(300);
      }
    }
    expect(ordered.flatMap(item => item.stage.dialogueVariants ?? [])).toHaveLength(9);
  });

  it('gives every depot priority a distinct advantage and cost', () => {
    const choices = CAMPAIGN.find(chapter => chapter.id === 'empty-shelves')!.stages.find(stage => stage.id === 'shipping')!.choices!;
    const metrics = ['care', 'trust', 'accountability'] as const;
    for (const candidate of choices) for (const alternative of choices) {
      if (candidate === alternative) continue;
      expect(metrics.some(metric => (candidate.effects?.[metric] ?? 0) > (alternative.effects?.[metric] ?? 0))).toBe(true);
      expect(metrics.some(metric => (candidate.effects?.[metric] ?? 0) < (alternative.effects?.[metric] ?? 0))).toBe(true);
    }
  });

  it('shows separate original records and preserves disclosure status', () => {
    const compare = CAMPAIGN.find(chapter => chapter.id === 'two-copies')!.stages.find(stage => stage.id === 'compare')!;
    expect(compare.documents).toEqual(['orderPublic', 'amendmentPublic']);
    expect(EVIDENCE.orderPublic!.body).toContain('twelve');
    expect(EVIDENCE.amendmentPublic!.body).toContain('Eight');
    const disclosed: StoryDecision = { chapterId: 'first-edition', stageId: 'friendly-ledger', choiceId: 'disclose' };
    const coalition: StoryDecision = { chapterId: 'public-hearing', stageId: 'hearing-choice', choiceId: 'our-side' };
    expect(getDocumentStatus('sponsor', [])).toContain('Known to the crew');
    expect(getDocumentStatus('sponsor', [disclosed, coalition])).toContain('Conflict disclosed publicly');
    expect(getDocumentStatus('hearing', [])).toContain('not an automatic public submission');
  });
});

describe('consequences and endings', () => {
  it('never contradicts an explicit settlement or coalition deal with a score-based ending', () => {
    const decision = (choiceId: string): StoryDecision[] => [{ chapterId: 'public-hearing', stageId: 'hearing-choice', choiceId }];
    expect(chooseEnding({ trust: 100, care: 100, accountability: 100 }, decision('settlement')).id).toBe('bargain');
    expect(chooseEnding({ trust: 100, care: 100, accountability: 100 }, decision('our-side')).id).toBe('different-chair');
    expect(chooseEnding({ trust: 100, care: 100, accountability: 100 }, decision('open-record')).id).toBe('open-windows');
    expect(chooseEnding({ trust: 10, care: 100, accountability: 100 }, decision('open-record')).id).toBe('broken-coalition');
    expect(chooseEnding({ trust: 60, care: 50, accountability: 60 }, decision('open-record')).id).toBe('unfinished-city');
  });

  it('can reach every authored ending through real campaign decisions', () => {
    let routes: { metrics: CampaignMetrics; history: StoryDecision[] }[] = [{ metrics: { trust: 50, care: 50, accountability: 50 }, history: [] }];
    for (const chapter of CAMPAIGN) for (const stage of chapter.stages) {
      if (!stage.choices) continue;
      routes = routes.flatMap(route => stage.choices!.map(choice => ({
        metrics: apply(route.metrics, choice.effects),
        history: [...route.history, { chapterId: chapter.id, stageId: stage.id, choiceId: choice.id }],
      })));
    }
    const endings = new Set(routes.map(route => chooseEnding(route.metrics, route.history).id));
    expect([...endings].sort()).toEqual(['bargain', 'broken-coalition', 'different-chair', 'open-windows', 'unfinished-city']);
    expect(routes).toHaveLength(2187);
  });
});
