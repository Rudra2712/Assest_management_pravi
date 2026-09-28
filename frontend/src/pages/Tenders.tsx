import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Gavel } from "lucide-react";
import { awardTender, cancelTender, closeBidding, createTender, listMyBids, listTenders, submitBid } from "../api/tenders";
import { listAdminUnits, listDepartments } from "../api/admin";
import { listAssets } from "../api/assets";
import { listProjects } from "../api/projects";
import { TenderStatusBadge } from "../components/Badge";
import { useAuth } from "../hooks/useAuth";
import type { Tender } from "../types";

function TenderCard({ tender }: { tender: Tender }) {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [bidAmount, setBidAmount] = useState("");
  const [bidRemarks, setBidRemarks] = useState("");

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["tenders"] });
    queryClient.invalidateQueries({ queryKey: ["my-bids"] });
  };
  const bidMutation = useMutation({
    mutationFn: () => submitBid(tender.id, Number(bidAmount), bidRemarks || undefined),
    onSuccess: () => {
      invalidate();
      setBidAmount("");
      setBidRemarks("");
    },
  });
  const closeMutation = useMutation({ mutationFn: () => closeBidding(tender.id), onSuccess: invalidate });
  const awardMutation = useMutation({ mutationFn: (bidId: string) => awardTender(tender.id, bidId), onSuccess: invalidate });
  const cancelMutation = useMutation({ mutationFn: () => cancelTender(tender.id), onSuccess: invalidate });

  const canManage = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");
  const isContractor = hasRole("CONTRACTOR");
  const myExistingBid = user?.contractor_id ? tender.bids.find((b) => b.contractor_id === user.contractor_id) : undefined;
  const canBid = isContractor && tender.status === "PUBLISHED" && !!user?.contractor_id && !myExistingBid;

  return (
    <div className="bg-white rounded-xl border border-slate-100 p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs font-mono text-slate-400">{tender.tender_number}</div>
          <div className="font-semibold text-ink">{tender.title}</div>
        </div>
        <TenderStatusBadge status={tender.status} />
      </div>
      <p className="text-sm text-slate-600">{tender.description}</p>
      <div className="text-xs text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
        {tender.estimated_value && <span>Estimated value: ₹{tender.estimated_value.toLocaleString()}</span>}
        {tender.submission_deadline && <span>Deadline: {tender.submission_deadline}</span>}
        {canManage || tender.status !== "PUBLISHED"
          ? <span>{tender.bid_count} bid{tender.bid_count === 1 ? "" : "s"}</span>
          : <span>Bid totals hidden until closing</span>}
      </div>

      {tender.bids.length > 0 && (
        <table className="w-full text-xs border-t border-slate-100 pt-2">
          <thead className="text-slate-400">
            <tr>
              <th className="text-left font-normal py-1">Contractor</th>
              <th className="text-left font-normal py-1">Amount</th>
              <th className="text-left font-normal py-1">Status</th>
              {canManage && tender.status === "BIDDING_CLOSED" && <th></th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {tender.bids.map((b) => (
              <tr key={b.id} className={b.status === "AWARDED" ? "bg-emerald-50" : ""}>
                <td className="py-1.5">{b.contractor_name ?? "Contractor"}</td>
                <td className="py-1.5">₹{b.bid_amount.toLocaleString()}</td>
                <td className="py-1.5">{b.status}</td>
                {canManage && tender.status === "BIDDING_CLOSED" && (
                  <td className="py-1.5">
                    <button onClick={() => awardMutation.mutate(b.id)} className="text-ink hover:underline flex items-center gap-1">
                      <Gavel size={11} /> Award
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {isContractor && tender.status === "PUBLISHED" && !user?.contractor_id && (
        <div className="text-xs text-amber-700 bg-amber-50 rounded-md px-2 py-1.5">
          Your account isn't linked to a contractor profile yet — ask an administrator to link one before you can bid.
        </div>
      )}
      {myExistingBid && (
        <div className="text-xs text-emerald-700 bg-emerald-50 rounded-md px-2 py-1.5">
          You already bid ₹{myExistingBid.bid_amount.toLocaleString()} on this tender ({myExistingBid.status}).
        </div>
      )}
      {tender.status === "AWARDED" && tender.bids.find((bid) => bid.id === tender.awarded_bid_id) && (
        <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
          Award announced: {tender.bids.find((bid) => bid.id === tender.awarded_bid_id)?.contractor_name} · ₹{tender.bids.find((bid) => bid.id === tender.awarded_bid_id)?.bid_amount.toLocaleString()}
        </div>
      )}
      {canBid && (
        <div className="flex gap-2 pt-2 border-t border-slate-100">
          <input type="number" placeholder="Your bid amount (₹)" value={bidAmount} onChange={(e) => setBidAmount(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm flex-1" />
          <input placeholder="Remarks" value={bidRemarks} onChange={(e) => setBidRemarks(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm flex-1" />
          <button disabled={!bidAmount || bidMutation.isPending} onClick={() => bidMutation.mutate()} className="bg-brand text-brand-ink text-sm font-semibold px-3 py-1.5 rounded-md disabled:opacity-50">
            Submit Bid
          </button>
        </div>
      )}
      {bidMutation.isError && <div className="text-xs text-red-600">Could not submit bid. Please refresh and try again.</div>}

      {canManage && tender.status === "PUBLISHED" && (
        <div className="flex gap-2 pt-2 border-t border-slate-100">
          <button onClick={() => closeMutation.mutate()} className="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-50">Close Bidding</button>
          <button onClick={() => cancelMutation.mutate()} className="text-xs px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50">Cancel Tender</button>
        </div>
      )}
    </div>
  );
}

export default function Tenders() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const isContractor = hasRole("CONTRACTOR");
  const canCreate = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [administrativeUnitId, setAdministrativeUnitId] = useState("");
  const [assetId, setAssetId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [estimatedValue, setEstimatedValue] = useState("");
  const [submissionDeadline, setSubmissionDeadline] = useState("");
  const [view, setView] = useState<"ALL" | "MY_BIDS">("ALL");

  const { data: tenders, isLoading } = useQuery({ queryKey: ["tenders"], queryFn: () => listTenders() });
  const { data: myBids } = useQuery({ queryKey: ["my-bids"], queryFn: listMyBids, enabled: isContractor });
  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: listDepartments, enabled: canCreate });
  const { data: adminUnits } = useQuery({ queryKey: ["admin-units"], queryFn: listAdminUnits, enabled: canCreate });
  const { data: assets } = useQuery({ queryKey: ["assets-for-tender"], queryFn: () => listAssets({ page_size: 200 }), enabled: canCreate });
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: listProjects, enabled: canCreate });

  const createMutation = useMutation({
    mutationFn: () =>
      createTender({
        title, description, department_id: departmentId, administrative_unit_id: administrativeUnitId,
        asset_id: assetId || undefined, project_id: projectId || undefined,
        estimated_value: estimatedValue ? Number(estimatedValue) : undefined,
        submission_deadline: submissionDeadline || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenders"] });
      setShowCreate(false);
      setTitle(""); setDescription(""); setEstimatedValue(""); setSubmissionDeadline("");
    },
  });

  const visibleTenders = isContractor && view === "ALL"
    ? tenders?.filter((tender) => tender.status === "PUBLISHED")
    : isContractor && view === "MY_BIDS"
      ? myBids
      : tenders;

  return (
    <div className="space-y-4">
      <div className="page-header">
        <div>
          <h1 className="page-title">Tenders (GeM)</h1>
          <p className="page-subtitle">Published works, contractor submissions and announced awards.</p>
        </div>
        {canCreate && <button onClick={() => setShowCreate((s) => !s)} className="bg-ink text-white text-sm font-medium px-4 py-2 rounded-md">+ Publish Tender</button>}
      </div>

      {isContractor && (
        <div className="inline-flex w-fit rounded-md border border-slate-300 bg-white p-1">
          <button type="button" aria-pressed={view === "ALL"} onClick={() => setView("ALL")} className={`rounded px-3 py-1.5 text-sm ${view === "ALL" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"}`}>Open tenders</button>
          <button type="button" aria-pressed={view === "MY_BIDS"} onClick={() => setView("MY_BIDS")} className={`rounded px-3 py-1.5 text-sm ${view === "MY_BIDS" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"}`}>My bids</button>
        </div>
      )}

      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-100 p-4 space-y-3">
          <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <textarea placeholder="Scope of work" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <div className="grid grid-cols-3 gap-3">
            <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Department…</option>
              {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
            <select value={administrativeUnitId} onChange={(e) => setAdministrativeUnitId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Administrative unit…</option>
              {adminUnits?.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
            </select>
            <select value={assetId} onChange={(e) => setAssetId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Linked asset (optional)…</option>
              {assets?.items.map((a) => <option key={a.id} value={a.id}>{a.asset_code} — {a.name}</option>)}
            </select>
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Linked project (optional)…</option>
              {projects?.map((p) => <option key={p.id} value={p.id}>{p.project_code} — {p.name}</option>)}
            </select>
            <input type="number" placeholder="Estimated value (₹)" value={estimatedValue} onChange={(e) => setEstimatedValue(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
            <input type="date" placeholder="Submission deadline" value={submissionDeadline} onChange={(e) => setSubmissionDeadline(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          </div>
          <button
            disabled={!title || !description || !departmentId || !administrativeUnitId || createMutation.isPending}
            onClick={() => createMutation.mutate()}
            className="bg-brand text-brand-ink text-sm font-semibold px-3 py-1.5 rounded-md disabled:opacity-50"
          >
            Publish
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {isLoading && <div className="text-slate-400">Loading…</div>}
        {visibleTenders?.map((t) => <TenderCard key={t.id} tender={t} />)}
        {!isLoading && !visibleTenders?.length && (
          <div className="text-slate-400 text-sm">{view === "MY_BIDS" ? "You have not submitted bids yet." : "No tenders published yet."}</div>
        )}
      </div>
    </div>
  );
}
