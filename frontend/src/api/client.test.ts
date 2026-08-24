import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet, apiPost } from "./client";

describe("apiGet", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("resolves with parsed JSON on a successful response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ticker: "NVDA" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiGet<{ ticker: string }>("/trades");

    expect(result).toEqual({ ticker: "NVDA" });
  });

  it("throws ApiError on a non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404, statusText: "Not Found" }),
    );

    await expect(apiGet("/trades")).rejects.toBeInstanceOf(ApiError);
  });

  it("only includes truthy query params", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    vi.stubGlobal("fetch", fetchMock);

    await apiGet("/trades", { ticker: "NVDA", politician_id: "" });

    const requestedUrl = fetchMock.mock.calls[0][0] as URL;
    expect(requestedUrl.searchParams.get("ticker")).toBe("NVDA");
    expect(requestedUrl.searchParams.has("politician_id")).toBe(false);
  });
});

describe("apiPost", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends a JSON body and resolves with the parsed response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "abc" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiPost<{ id: string }>("/recommendations/1/simulated-orders", {
      side: "buy",
      quantity: 5,
      price: 100,
    });

    expect(result).toEqual({ id: "abc" });
    const [url, init] = fetchMock.mock.calls[0] as [string, { method: string; body: string }];
    expect(url).toContain("/recommendations/1/simulated-orders");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ side: "buy", quantity: 5, price: 100 });
  });

  it("throws ApiError on a non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 422, statusText: "Unprocessable Entity" }),
    );

    await expect(apiPost("/recommendations/1/simulated-orders", {})).rejects.toBeInstanceOf(
      ApiError,
    );
  });
});
