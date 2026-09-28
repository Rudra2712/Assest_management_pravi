import { api } from "./client";
import type { Tender, TenderBid } from "../types";

export async function listTenders(params: Record<string, string | undefined> = {}): Promise<Tender[]> {
  const res = await api.get<Tender[]>("/tenders", { params });
  return res.data;
}

export async function listMyBids(): Promise<Tender[]> {
  const res = await api.get<Tender[]>("/tenders/my-bids");
  return res.data;
}

export async function getTender(id: string): Promise<Tender> {
  const res = await api.get<Tender>(`/tenders/${id}`);
  return res.data;
}

export async function createTender(payload: Record<string, unknown>): Promise<Tender> {
  const res = await api.post<Tender>("/tenders", payload);
  return res.data;
}

export async function submitBid(tenderId: string, bidAmount: number, remarks?: string): Promise<TenderBid> {
  const res = await api.post<TenderBid>(`/tenders/${tenderId}/bids`, { bid_amount: bidAmount, remarks });
  return res.data;
}

export async function closeBidding(tenderId: string): Promise<Tender> {
  const res = await api.post<Tender>(`/tenders/${tenderId}/close`);
  return res.data;
}

export async function awardTender(tenderId: string, bidId: string): Promise<Tender> {
  const res = await api.post<Tender>(`/tenders/${tenderId}/award`, { bid_id: bidId });
  return res.data;
}

export async function cancelTender(tenderId: string): Promise<Tender> {
  const res = await api.post<Tender>(`/tenders/${tenderId}/cancel`);
  return res.data;
}
