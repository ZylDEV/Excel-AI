import React from "react";

interface Props {
  message?: string;
}

const LoadingSpinner: React.FC<Props> = ({ message = "Memproses..." }) => {
  return (
    <div className="loading-spinner">
      <div className="spinner" />
      <p className="spinner-message">{message}</p>
    </div>
  );
};

export default LoadingSpinner;
