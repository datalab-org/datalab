import Creators from "@/components/Creators.vue";

describe("Creators.vue", () => {
  const mockCreators = [
    { display_name: "Test display_name 1" },
    { display_name: "Test display_name 2" },
    { display_name: "Test display_name 3" },
  ];

  it("should display the names of creators when showNames is true", () => {
    cy.mount(Creators, {
      props: {
        creators: mockCreators,
        showNames: true,
        showBubble: false,
      },
    });

    mockCreators.forEach((creator) => {
      cy.contains(creator.display_name).should("exist");
    });

    cy.get(".display-name").then((elements) => {
      expect(elements[0].innerText).to.contain(mockCreators[0].display_name);
      expect(elements[1].innerText).to.contain(mockCreators[1].display_name);
      expect(elements[2].innerText).to.contain(mockCreators[2].display_name);
    });
  });

  it("should not display names if showNames is false", () => {
    cy.mount(Creators, {
      props: {
        creators: mockCreators,
        showNames: false,
        showBubble: true,
      },
    });

    mockCreators.forEach((creator) => {
      cy.get(".creators-container")
        .find(":not([data-testid='styled-tooltip'])")
        .should("not.contain", creator.display_name);
    });
  });

  it("should display user bubbles when showBubble is true", () => {
    cy.mount(Creators, {
      props: {
        creators: mockCreators,
        showNames: false,
        showBubble: true,
      },
    });

    cy.get("img").should("have.length", mockCreators.length);
  });

  it("should not display user bubbles if showBubble is false", () => {
    cy.mount(Creators, {
      props: {
        creators: mockCreators,
        showNames: true,
        showBubble: false,
      },
    });

    cy.get("img").should("not.exist");
  });

  it("should display nothing when creators list is empty", () => {
    cy.mount(Creators, {
      props: {
        creators: [],
        showNames: true,
        showBubble: true,
      },
    });

    cy.get("span").should("not.exist");
  });

  it("should display user bubbles with the correct size", () => {
    const customSize = 32;

    cy.mount(Creators, {
      props: {
        creators: mockCreators,
        showNames: false,
        showBubble: true,
        size: customSize,
      },
    });

    cy.get("img")
      .should("have.length", mockCreators.length)
      .then(($images) => {
        $images.each((index, img) => {
          const imgStyle = window.getComputedStyle(img);
          expect(imgStyle.width).to.eq(`${customSize}px`);
          expect(imgStyle.height).to.eq(`${customSize}px`);
        });
      });
  });
});
