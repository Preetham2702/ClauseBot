import { useEffect, useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";

// PDF.js imports for Vite
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf";
import pdfjsWorker from "pdfjs-dist/build/pdf.worker.js?url";

// Set PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export default function LeftPanel({
  onFileUpload,
  pdfUrl,
  onClear,                 // ✅ NEW
  pageAnnotations = {},
}) {
  const [pages, setPages] = useState([]);
  const [activePage, setActivePage] = useState(null);

  /** ESC to close modal */
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") setActivePage(null);
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, []);

  /** ----- FILE DROP HANDLER ----- **/
  const handleDrop = useCallback(
    (files) => {
      if (files?.length > 0) {
        onFileUpload(files[0]);
      }
    },
    [onFileUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    multiple: false,
    accept: { "application/pdf": [] },
  });

  /** ----- PDF RENDER ----- **/
  useEffect(() => {
    if (!pdfUrl) {
      setPages([]);
      return;
    }

    async function renderPdf() {
      try {
        const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
        const imgs = [];

        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const viewport = page.getViewport({ scale: 0.7 });

          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");

          canvas.width = viewport.width;
          canvas.height = viewport.height;

          await page.render({
            canvasContext: ctx,
            viewport,
          }).promise;

          imgs.push(canvas.toDataURL());
        }

        setPages(imgs);
      } catch (err) {
        console.error("PDF render error:", err);
      }
    }

    renderPdf();
  }, [pdfUrl]);

  /** ----- HIGHLIGHT BAR COLORS ----- **/
  const getBarColor = (tag) => {
    switch (tag) {
      case "summary":
        return "rgba(255, 120, 120, 0.65)";
      case "pros":
        return "rgba(120, 255, 170, 0.65)";
      case "cons":
        return "rgba(255, 70, 70, 0.70)";
      case "important_points":
        return "rgba(255, 220, 120, 0.75)";
      default:
        return "rgba(160, 160, 160, 0.45)";
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-[#121212] text-white overflow-hidden">
      {/* HEADER */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#2A2A2A]">
        <h2 className="font-semibold text-lg">Document</h2>

        {/* ✅ CLEAR BUTTON */}
        {pdfUrl && (
          <button
            onClick={() => {
              setActivePage(null);
              onClear?.();
            }}
            className="
              text-xs px-3 py-1 rounded-full
              bg-[#2A2A2A] hover:bg-[#ff4d4d]
              transition
            "
          >
            Clear
          </button>
        )}
      </div>

      {/* BEFORE UPLOAD */}
      {!pdfUrl && (
        <div className="flex flex-1 items-center justify-center">
          <div
            {...getRootProps()}
            className={`
              w-[240px] h-[280px]
              border-2 border-dashed rounded-xl cursor-pointer
              flex flex-col items-center justify-center
              text-center transition
              ${
                isDragActive
                  ? "border-red-400 bg-[#1C1C1C]"
                  : "border-[#444] bg-[#181818]"
              }
            `}
          >
            <input {...getInputProps()} />

            <img
              src="https://cdn-icons-png.flaticon.com/512/337/337946.png"
              className="w-10 opacity-80 mb-3"
              alt="pdf"
            />

            <p className="text-sm text-[#AAAAAA] leading-relaxed">
              Drag & drop PDF<br />or click to upload
            </p>
          </div>
        </div>
      )}

      {/* AFTER UPLOAD */}
      {pdfUrl && (
        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-6">
          {pages.map((src, index) => {
            const pageNumber = index + 1;
            const tags = pageAnnotations[pageNumber] || [];

            return (
              <div
                key={index}
                className="relative cursor-pointer"
                onClick={() => setActivePage({ src, tags, pageNumber })}
              >
                {/* Page Image */}
                <img
                  src={src}
                  className="w-full rounded-lg shadow-md border border-[#333]"
                  alt={`page-${pageNumber}`}
                />

                {/* Highlight Bars */}
                {tags.map((tag, i) => (
                  <div
                    key={i}
                    className="absolute left-2 right-2 h-3 rounded"
                    style={{
                      top: `${i * 12 + 8}px`,
                      background: getBarColor(tag),
                    }}
                  />
                ))}
              </div>
            );
          })}
        </div>
      )}

      {/* MODAL */}
      {activePage && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-6 py-6"
          onClick={() => setActivePage(null)}
        >
          <div
            className="relative bg-[#1B1B1B] p-6 rounded-2xl shadow-xl max-w-5xl w-full"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              className="absolute top-3 right-3 text-white text-2xl hover:text-red-400"
              onClick={() => setActivePage(null)}
            >
              ✕
            </button>

            {/* Title */}
            <p className="text-gray-400 mb-3">Page {activePage.pageNumber}</p>

            {/* Image */}
            <div className="relative">
              <img
                src={activePage.src}
                className="w-full rounded-xl border border-[#444]"
                alt={`modal-page-${activePage.pageNumber}`}
              />

              {/* Highlight Bars in Modal */}
              {activePage.tags.map((tag, i) => (
                <div
                  key={i}
                  className="absolute left-3 right-3 h-4 rounded"
                  style={{
                    top: `${i * 18 + 12}px`,
                    background: getBarColor(tag),
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
