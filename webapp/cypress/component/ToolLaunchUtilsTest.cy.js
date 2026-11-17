import { parseToolLaunchUrl } from "@/tool_launch_utils.js";

describe("parseToolLaunchUrl", () => {
  [
    ["remote HTTPS", "https://tools.example.test/start", "https://tools.example.test/start"],
    ["localhost HTTP", "http://localhost:8080/start", "http://localhost:8080/start"],
    ["localhost subdomain HTTP", "http://a.localhost/start", "http://a.localhost/start"],
    ["IPv4 loopback HTTP", "http://127.0.0.1/start", "http://127.0.0.1/start"],
    ["127/8 HTTP", "http://127.42.0.9/start", "http://127.42.0.9/start"],
    ["IPv6 loopback HTTP", "http://[::1]:8080/start", "http://[::1]:8080/start"],
  ].forEach(([description, value, expected]) => {
    it(`accepts ${description}`, () => {
      expect(parseToolLaunchUrl(value)).to.equal(expected);
    });
  });

  [
    ["remote HTTP", "http://tools.example.test/start"],
    ["private-network HTTP", "http://192.168.1.20/start"],
    ["a localhost lookalike", "http://localhost.example.com/start"],
    ["embedded HTTPS credentials", "https://user:secret@tools.example.test/start"],
    ["embedded loopback HTTP credentials", "http://user:secret@localhost/start"],
    ["a non-HTTP(S) scheme", "javascript:alert(1)"],
  ].forEach(([description, value]) => {
    it(`rejects ${description}`, () => {
      expect(() => parseToolLaunchUrl(value)).to.throw("unsafe launch URL");
    });
  });
});
