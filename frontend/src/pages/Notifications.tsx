import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listNotifications, markNotificationRead } from "../api/notifications";

export default function Notifications() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["notifications"], queryFn: () => listNotifications(false) });
  const readMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-slate-900">Notifications</h1>
      <div className="bg-white rounded-lg border border-slate-200 divide-y divide-slate-100">
        {isLoading && <div className="p-4 text-slate-400">Loading…</div>}
        {data?.map((n) => (
          <div key={n.id} className={`p-4 flex justify-between items-start ${n.is_read ? "opacity-60" : ""}`}>
            <div>
              <div className="text-sm font-medium text-slate-900">{n.title}</div>
              {n.body && <div className="text-sm text-slate-500">{n.body}</div>}
              <div className="text-xs text-slate-400 mt-1">{new Date(n.created_at).toLocaleString()}</div>
            </div>
            {!n.is_read && (
              <button onClick={() => readMutation.mutate(n.id)} className="text-xs text-rb-navy hover:underline shrink-0 ml-3">
                Mark read
              </button>
            )}
          </div>
        ))}
        {!isLoading && !data?.length && <div className="p-4 text-slate-400 text-sm">No notifications.</div>}
      </div>
    </div>
  );
}
