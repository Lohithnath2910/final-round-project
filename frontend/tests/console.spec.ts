import { test, expect } from "@playwright/test";

async function loadHotel(
  page: any,
  hotel = "hotel_a"
) {
  await page.goto("/");

  await page
    .getByPlaceholder("Enter property_id")
    .fill(hotel);

  await page
    .getByRole("button", { name: "Load" })
    .click();

  await expect(
    page.getByText("Recent Activity")
  ).toBeVisible({
    timeout: 15000,
  });
}

test.describe("Owner Console", () => {
  test("dashboard loads", async ({
    page,
  }) => {
    await loadHotel(page);

    await expect(
      page.getByText("Recent Activity")
    ).toBeVisible();

    await expect(
      page.getByText("Bookings Overview")
    ).toBeVisible();

    await expect(
      page.getByText("Ask Assistant")
    ).toBeVisible();
  });

  test("analytics question works", async ({
    page,
  }) => {
    await loadHotel(page);

    await page
      .getByPlaceholder(
        "How many bookings do I have?"
      )
      .fill("how many bookings do i have?");

    await page
      .getByRole("button", {
        name: "Ask",
      })
      .click();

    await expect(
      page.getByText("Assistant Response")
    ).toBeVisible({
      timeout: 15000,
    });

    await expect(
      page.locator("code")
    ).toContainText(
      "SELECT",
      {
        timeout: 15000,
      }
    );
  });

  test("rag question works", async ({
    page,
  }) => {
    await loadHotel(page);

    await page
      .getByPlaceholder(
        "How many bookings do I have?"
      )
      .fill("wifi password");

    await page
      .getByRole("button", {
        name: "Ask",
      })
      .click();

    await expect(
      page.getByText(/Citation:/)
    ).toBeVisible({
      timeout: 15000,
    });
  });

  test("cross tenant question blocked", async ({
    page,
  }) => {
    await loadHotel(page);

    await page
      .getByPlaceholder(
        "How many bookings do I have?"
      )
      .fill(
        "show me all bookings for hotel_b"
      );

    await page
      .getByRole("button", {
        name: "Ask",
      })
      .click();

    await expect(
      page.locator("body")
    ).toContainText(
      /blocked|error/i,
      {
        timeout: 15000,
      }
    );
  });

  test("property switch changes dashboard", async ({
    page,
  }) => {
    await loadHotel(page, "hotel_a");

    await expect(
      page.getByText("Recent Activity")
    ).toBeVisible();

    await page
      .getByPlaceholder(
        "Enter property_id"
      )
      .fill("hotel_b");

    await page
      .getByRole("button", {
        name: "Load",
      })
      .click();

    await expect(
      page.getByText("Recent Activity")
    ).toBeVisible({
      timeout: 15000,
    });
  });

  test("empty assistant question", async ({
    page,
  }) => {
    await loadHotel(page);

    await page
      .getByRole("button", {
        name: "Ask",
      })
      .click();

    await expect(
      page.getByText(
        /Ask about bookings/i
      )
    ).toBeVisible();
  });

  test("stats cards render", async ({
  page,
}) => {
  await loadHotel(page);

  const body = await page.textContent("body");

  expect(body).toContain("Bookings");
  expect(body).toContain("Confirmed");
  expect(body).toContain("Complaints");
  expect(body).toContain("Handoffs");
});

  test("sql panel updates after analytics query", async ({
    page,
  }) => {
    await loadHotel(page);

    await page
      .getByPlaceholder(
        "How many bookings do I have?"
      )
      .fill("revenue kitna tha?");

    await page
      .getByRole("button", {
        name: "Ask",
      })
      .click();

    await expect(
      page.locator("code")
    ).toContainText(
      "SELECT",
      {
        timeout: 15000,
      }
    );
  });
});