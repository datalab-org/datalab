import SampleTable from "@/components/SampleTable";
import { render } from "@testing-library/vue";
import store from "@/store/index";
import { API_URL } from "@/resources.js";

beforeEach(() => {
  fetch.resetMocks();
});

var globalPropertiesMock = {
  $API_URL: API_URL,
  $filters: {
    IsoDatetimeToDate(isodatetime) {
      if (isodatetime) {
        return isodatetime.substring(0, 10);
      }
      return isodatetime; // if isodatetime is null or empty, don't do anything
    },
  },
};

test("it renders correctly with 0 samples", () => {
  fetch.mockResponseOnce(
    JSON.stringify({
      samples: [],
    })
  );

  const { getByText, container } = render(SampleTable, {
    global: {
      plugins: [store],
      mocks: globalPropertiesMock,
    },
  });

  getByText("Sample name");
  expect(container).toMatchSnapshot();
});

test("it renders correctly with some samples", async () => {
  await fetch.mockResponseOnce(
    JSON.stringify({
      samples: [
        {
          chemform: "In0.333WO3",
          date: "2020-02-17T00:00",
          name: "This is a test sample",
          nblocks: 6,
          type: "samples",
          item_id: "jdb1-1",
        },
        {
          chemform: "NaCoO2",
          date: "2021-02-19T08:00",
          name: "in situ SQUID test",
          nblocks: 1,
          type: "cells",
          item_id: "jdb11-3_e1_s2",
        },
        {
          date: "2021-02-24T09:23",
          name: "another in situ SQUID test",
          nblocks: 1,
          type: "cells",
          item_id: "jdb11-3_e1_s3",
        },
        {
          date: "1954-01-01T22:22",
          name: " ",
          nblocks: 0,
          type: "samples",
          item_id: "empty_test",
        },
      ],
    })
  );

  const { findByText, container } = render(SampleTable, {
    global: {
      plugins: [store],
      mocks: globalPropertiesMock,
    },
  });
  // console.log(rendered.container)

  await findByText("jdb1-1");
  await findByText("jdb11-3_e1_s2");
  await findByText("jdb11-3_e1_s3");
  await findByText("empty_test");

  // await expect(container).toMatchSnapshot();
});
