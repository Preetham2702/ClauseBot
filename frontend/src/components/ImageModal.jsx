import React from "react";

export default function ImageModal({ src, tags = [], onClose }) {
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="relative bg-[#1a1a1a] p-4 rounded-2xl shadow-xl max-w-4xl w-full">

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-white text-xl hover:text-red-400"
        >
          ✕
        </button>

        {/* Image Container */}
        <div className="relative mx-auto">
          <img
            src={src}
            className="w-full rounded-xl border border-gray-600"
          />

          {/* Summary */}
          {tags.includes("summary") && (
            <div className="absolute top-2 left-2 right-2 h-3 bg-red-300/70 rounded"></div>
          )}

          {/* Pros */}
          {tags.includes("pros") && (
            <div className="absolute top-7 left-2 right-2 h-3 bg-green-300/70 rounded"></div>
          )}

          {/* Cons */}
          {tags.includes("cons") && (
            <div className="absolute top-12 left-2 right-2 h-3 bg-red-500/70 rounded"></div>
          )}

          {/* Important Points */}
          {tags.includes("important_points") && (
            <div className="absolute top-[70px] left-2 right-2 h-3 bg-yellow-300/70 rounded"></div>
          )}
        </div>
      </div>
    </div>
  );
}
