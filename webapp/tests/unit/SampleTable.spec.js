import SampleTable from "@/components/SampleTable";
import { render } from "@testing-library/vue";

test("it renders correctly", () => {
  const { getByText } = render(SampleTable);
  getByText("Sample name");
});
