import SampleTable from "@/components/SampleTable";
import { render } from "@testing-library/vue";
import store from "@/store/index";

beforeEach(() => {
  fetch.resetMocks();
});

// function renderSampleTable(customStore) {
//   // Render the component and merge the original store and the custom one
//   // provided as a parameter. This way, we can alter some behaviors of the
//   // initial implementation.
//   return render(SampleTable, {store: {...store, ...customStore}})
// }

// jest.mock("@/server_fetch_utils")

test("it renders correctly with 0 samples", () => {
  fetch.mockResponseOnce(JSON.stringify({ samples: [] }));

  const { getByText, container } = render(SampleTable, {
    global: {
      plugins: [store],
    },
  });

  getByText("Sample name");
  expect(container).toMatchSnapshot();
});

test("it renders correctly with some samples", async () => {
  fetch.mockResponseOnce(
    JSON.stringify({
      samples: [
        {
          chemform: "In0.333WO3",
          date: "2021-02-17",
          name: "This is a test sample",
          nblocks: 6,
          sample_id: "jdb1-1",
        },
        {
          chemform: "NaCoO2",
          date: "2021-02-19",
          name: "in situ SQUID test",
          nblocks: 1,
          sample_id: "jdb11-3_e1_s2",
        },
        {
          date: "2021-02-24",
          name: "another in situ SQUID test",
          nblocks: 1,
          sample_id: "jdb11-3_e1_s3",
        },
      ],
    })
  );

  const { findByText, container } = render(SampleTable, {
    global: {
      plugins: [store],
    },
  });
  // console.log(rendered.container)

  await findByText("jdb1-1");
  await findByText("jdb11-3_e1_s2");
  await findByText("jdb11-3_e1_s3");

  expect(container).toMatchSnapshot();
});

