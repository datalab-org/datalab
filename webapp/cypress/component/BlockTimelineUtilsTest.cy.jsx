import { blockTimestamp, groupBlocksByDay } from "@/block_timeline.js";

describe("block_timeline.js", () => {
  describe("blockTimestamp", () => {
    it("prefers the measurement time over the creation time", () => {
      const block = {
        metadata: { measured_at: "2023-10-23T16:11:12+00:00" },
        created_at: "2026-11-06T10:00:00+00:00",
      };
      expect(blockTimestamp(block).toISOString()).to.equal("2023-10-23T16:11:12.000Z");
    });

    it("falls back to the creation time", () => {
      const block = { metadata: { nucleus: "1H" }, created_at: "2026-11-06T10:00:00" };
      expect(blockTimestamp(block).toISOString()).to.equal("2026-11-06T10:00:00.000Z");
    });

    it("returns null when no date is available or parseable", () => {
      expect(blockTimestamp({})).to.equal(null);
      expect(blockTimestamp(undefined)).to.equal(null);
      expect(blockTimestamp({ created_at: "not a date" })).to.equal(null);
    });
  });

  describe("groupBlocksByDay", () => {
    const blocksObj = {
      comment: { created_at: "2026-11-06T09:00:00Z" },
      xrd: {
        metadata: { measured_at: "2023-10-23T16:00:00Z" },
        created_at: "2026-11-05T09:00:00Z",
      },
      nmr: {
        metadata: { measured_at: "2023-10-23T08:00:00Z" },
        created_at: "2026-11-05T10:00:00Z",
      },
      legacy: { blocktype: "comment" },
      legacy2: { blocktype: "media" },
    };

    it("sorts blocks oldest first and groups them by day, with undated blocks last", () => {
      const groups = groupBlocksByDay(["legacy", "comment", "xrd", "legacy2", "nmr"], blocksObj);

      expect(groups.map((g) => g.blockIds)).to.deep.equal([
        ["nmr", "xrd"],
        ["comment"],
        ["legacy", "legacy2"],
      ]);
      expect(groups[0].date).to.be.instanceOf(Date);
      expect(groups[2].date).to.equal(null);
      expect(groups[2].key).to.equal("undated");
    });

    it("keeps the manual order for blocks with identical timestamps", () => {
      const sameTime = {
        a: { created_at: "2026-11-06T09:00:00Z" },
        b: { created_at: "2026-11-06T09:00:00Z" },
      };
      expect(groupBlocksByDay(["b", "a"], sameTime)[0].blockIds).to.deep.equal(["b", "a"]);
    });

    it("does not mutate the display order", () => {
      const displayOrder = ["comment", "xrd"];
      groupBlocksByDay(displayOrder, blocksObj);
      expect(displayOrder).to.deep.equal(["comment", "xrd"]);
    });

    it("handles empty or missing inputs", () => {
      expect(groupBlocksByDay([], {})).to.deep.equal([]);
      expect(groupBlocksByDay(undefined, undefined)).to.deep.equal([]);
    });
  });
});
