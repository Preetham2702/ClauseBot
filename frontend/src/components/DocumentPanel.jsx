import React, { useState } from "react";
import PageThumbnail from "./pagethumbnail";
import ImageModal from "./ImageModal";

export default function DocumentPanel({ pages, pageAnnotations }) {

  const [activePage, setActivePage] = useState(null);

  return (
    <div className="w-full h-full overflow-y-auto p-4 space-y-4">

      {/* Pages */}
      {pages.map((src, index) => {
        const pageNumber = index + 1;
        const tags = pageAnnotations[pageNumber] || [];

        return (
          <PageThumbnail
            key={index}
            src={src}
            tags={tags}
            onClick={() => setActivePage({ src, tags })}
          />
        );
      })}

      {/* Modal */}
      {activePage && (
        <ImageModal
          src={activePage.src}
          tags={activePage.tags}
          onClose={() => setActivePage(null)}
        />
      )}
    </div>
  );
}
