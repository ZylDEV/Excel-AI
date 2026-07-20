import React from "react";
import { AlertTriangle, X } from "lucide-react";

interface Props {
  message: string;
  onDismiss?: () => void;
}

const ErrorAlert: React.FC<Props> = ({ message, onDismiss }) => {
  return (
    <div className="error-alert">
      <span className="error-alert-icon">
        <AlertTriangle size={16} />
      </span>
      <span className="error-alert-text">{message}</span>
      {onDismiss && (
        <button className="error-alert-dismiss" onClick={onDismiss}>
          <X size={14} />
        </button>
      )}
    </div>
  );
};

export default ErrorAlert;
