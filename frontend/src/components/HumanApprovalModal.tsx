import { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { projects as projectsApi } from '../api/client';

interface ApprovalRequest {
  id: string;
  action: string;
  description: string;
}

export default function HumanApprovalModal({
  request,
  projectId,
  onClose,
}: {
  request: ApprovalRequest;
  projectId: string;
  onClose: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  async function handleApprove() {
    setLoading(true);
    try {
      await projectsApi.respondApproval(projectId, request.id, true);
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleReject() {
    if (!showRejectInput) { setShowRejectInput(true); return; }
    setLoading(true);
    try {
      await projectsApi.respondApproval(projectId, request.id, false, rejectionReason);
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-bg-base/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass w-full max-w-md p-8"
      >
        {/* Icon */}
        <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-accent-yellow/10 border border-accent-yellow/20 mx-auto mb-5">
          <AlertTriangle className="w-7 h-7 text-accent-yellow" />
        </div>

        <h2 className="text-lg font-semibold text-text-primary text-center mb-1">
          DevCrew Requires Your Approval
        </h2>
        <p className="text-text-secondary text-sm text-center mb-6">
          The pipeline has paused and is waiting for your decision.
        </p>

        {/* Action details */}
        <div className="bg-bg-raised border border-bg-border rounded-lg p-4 mb-5">
          <div className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Action</div>
          <div className="text-sm font-medium text-text-primary mb-2">{request.action}</div>
          <div className="text-xs text-text-secondary leading-relaxed">{request.description}</div>
        </div>

        {showRejectInput && (
          <div className="mb-4">
            <label className="label">Reason for rejection (optional)</label>
            <input
              className="input"
              placeholder="Explain why this action should not proceed…"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              autoFocus
            />
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleReject}
            id="approval-reject-btn"
            className="btn-danger flex-1 justify-center"
            disabled={loading}
          >
            {loading && showRejectInput ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
            {showRejectInput ? 'Confirm Reject' : 'Reject'}
          </button>
          <button
            onClick={handleApprove}
            id="approval-approve-btn"
            className="btn-success flex-1 justify-center"
            disabled={loading}
          >
            {loading && !showRejectInput ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
            Approve
          </button>
        </div>
      </motion.div>
    </div>
  );
}
