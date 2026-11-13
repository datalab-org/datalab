import { validateEntryID } from "@/field_utils.js";

describe("validateEntryID", () => {
  it("returns no error for a valid, unused ID", () => {
    expect(validateEntryID("valid_id-123")).to.equal("");
  });

  it("returns an edit link when the ID is already in use", () => {
    const msg = validateEntryID("taken_id", ["taken_id"]);
    expect(msg).to.contain("already in use");
    expect(msg).to.contain("<a href='edit/taken_id'>");
  });

  it("rejects disallowed characters", () => {
    expect(validateEntryID("bad id")).to.contain("alphanumeric");
  });

  // Regression test: the charset check must run before the "already in use" branch, so
  // a crafted ID can never reach the HTML interpolation even if it matches a taken ID.
  it("never emits raw HTML for an ID containing markup, even if 'taken'", () => {
    const payload = `x"><img src=x onerror=alert(1)>`;
    const msg = validateEntryID(payload, [payload], [payload]);
    expect(msg).to.not.contain("<img");
    expect(msg).to.not.contain("<a ");
    expect(msg).to.contain("alphanumeric");
  });
});
