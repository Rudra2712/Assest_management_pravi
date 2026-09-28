import { api } from "./client";
import type { NotificationItem } from "../types";

export async function listNotifications(unreadOnly = false): Promise<NotificationItem[]> {
  const res = await api.get<NotificationItem[]>("/notifications", { params: { unread_only: unreadOnly } });
  return res.data;
}

export async function markNotificationRead(id: string): Promise<NotificationItem> {
  const res = await api.post<NotificationItem>(`/notifications/${id}/read`);
  return res.data;
}
