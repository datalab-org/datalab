import fetchMock from "jest-fetch-mock";
import { API_URL } from "@/resources.js";
import { config } from "@vue/test-utils";

fetchMock.enableMocks();

// config.mocks["$API_URL"] = API_URL;
// config.mocks["$filters"] = {
//   IsoDatetimeToDate(isodatetime) {
//     if (isodatetime) {
//       return isodatetime.substring(0, 10);
//     }
//     return isodatetime; // if isodatetime is null or empty, don't do anything
//   },
// };
