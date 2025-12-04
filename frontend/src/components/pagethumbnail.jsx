import React from "react";

export default function PageThumbnail({ src, tags = [], onClick }) {
  return (
    <div
      className="relative cursor-pointer mb-4"
      onClick={onClick}
    >
      {/* Page Image */}
      <img
        src={src}
        className="w-full rounded-xl border border-gray-600"
      />

      {/* Summary */}
      {tags.includes("summary") && (
        <div className="absolute top-2 left-2 right-2 h-2 bg-red-300/70 rounded"></div>
      )}

      {/* Pros */}
      {tags.includes("pros") && (
        <div className="absolute top-5 left-2 right-2 h-2 bg-green-300/70 rounded"></div>
      )}

      {/* Cons */}
      {tags.includes("cons") && (
        <div className="absolute top-8 left-2 right-2 h-2 bg-red-500/70 rounded"></div>
      )}

      {/* Important Points */}
      {tags.includes("important_points") && (
        <div className="absolute top-11 left-2 right-2 h-2 bg-yellow-300/70 rounded"></div>
      )}
    </div>
  );
}
