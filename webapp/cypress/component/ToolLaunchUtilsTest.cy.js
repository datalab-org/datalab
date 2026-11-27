import { parseToolLaunchUrl } from "@/tool_launch_utils.js";

describe("parseToolLaunchUrl", () => {
  [
    ["remote HTTPS", "https://tools.example.test/start", "https://tools.example.test/start"],
    ["localhost HTTP", "http://localhost:8080/start", "http://localhost:8080/start"],
    ["127/8 HTTP", "http://127.42.0.9/start", "http://127.42.0.9/start"],
    ["IPv6 loopback HTTP", "http://[::1]:8080/start", "http://[::1]:8080/start"],
    ["remote HTTP", "http://tools.example.test/start", "http://tools.example.test/start"],
  ].forEach(([description, value, expected]) => {
    it(`accepts ${description}`, () => {
      expect(parseToolLaunchUrl(value)).to.equal(expected);
    });
  });

  [
    ["embedded HTTPS credentials", "https://user:secret@tools.example.test/start"],
    ["a non-HTTP(S) scheme", "javascript:alert(1)"],
  ].forEach(([description, value]) => {
    it(`rejects ${description}`, () => {
      expect(() => parseToolLaunchUrl(value)).to.throw("unsafe launch URL");
    });
  });
});
