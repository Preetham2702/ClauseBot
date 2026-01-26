import { useState, useRef, useEffect } from "react";
import { FiPlus, FiMic } from "react-icons/fi";
import { RxPaperPlane } from "react-icons/rx";

const API_BASE = "http://127.0.0.1:8000"; // change if your backend is different

export default function RightChatPanel() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hey there! Ask me anything." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const bottomRef = useRef(null);

  async function sendMessage() {
    const question = input.trim();
    if (!question || loading) return;

    // 1) add user message
    setMessages((prev) => [...prev, { sender: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      // 2) call backend
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await res.json();

      // 3) add bot message
      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: data?.detail || "Something went wrong." },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: data?.answer || "No answer returned." },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Backend not reachable (is FastAPI running?)" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="w-full h-full flex flex-col bg-[#1A1A1A]">
      {/* CHAT */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => {
          const isUser = msg.sender === "user";
          return (
            <div
              key={i}
              className={`flex items-end gap-2 w-full ${
                isUser ? "justify-end" : "justify-start"
              }`}
            >
              {!isUser && <span className="text-xl select-none">🤖</span>}

              <div
                className={`max-w-[70%] px-3 py-2 text-sm rounded-xl text-white ${
                  isUser ? "bg-[#2E2E2E]" : "bg-[#1E1E1E]"
                }`}
              >
                {msg.text}
              </div>

              {isUser && <span className="text-xl select-none">👤</span>}
            </div>
          );
        })}

        {/* typing bubble */}
        {loading && (
          <div className="flex items-end gap-2 w-full justify-start">
            <span className="text-xl select-none">🤖</span>
            <div className="max-w-[70%] px-3 py-2 text-sm rounded-xl text-white bg-[#1E1E1E] opacity-80">
              Typing...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* INPUT */}
      <div className="p-4 border-t border-[#2E2E2E] bg-[#1A1A1A]">
        <div className="w-full flex items-center gap-3 px-4 py-3 bg-[#2F2F2F] rounded-3xl shadow-lg">
          <FiPlus className="text-white text-xl cursor-pointer opacity-70 hover:opacity-100" />

          <input
            className="flex-1 bg-transparent text-[#EAEAEA] text-sm outline-none placeholder-[#9E9E9E]"
            placeholder="Ask anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={loading}
          />

          <FiMic className="text-white text-lg cursor-pointer opacity-70 hover:opacity-100" />

          <button
            onClick={sendMessage}
            disabled={loading}
            className="w-8 h-8 bg-white flex items-center justify-center rounded-full shadow-md hover:scale-105 transition disabled:opacity-60"
          >
            <RxPaperPlane className="text-black text-sm" />
          </button>
        </div>
      </div>
    </div>
  );
}
