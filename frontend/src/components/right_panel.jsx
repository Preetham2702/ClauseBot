import { useState, useRef, useEffect } from "react";
import { FiPlus, FiMic } from "react-icons/fi";
import { RxPaperPlane } from "react-icons/rx";

export default function RightChatPanel() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hey there! Ask me anything." }
  ]);
  const [input, setInput] = useState("");

  const bottomRef = useRef(null);

  // Send message
  const sendMessage = () => {
    if (!input.trim()) return;

    setMessages(prev => [...prev, { sender: "user", text: input }]);
    setInput("");
  };

  // Auto scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="w-full h-full flex flex-col bg-[#1A1A1A]">

      {/* CHAT HISTORY */}
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
              {/* Bot Icon */}
              {!isUser && (
                <span className="text-xl select-none">🤖</span>
              )}

              {/* Bubble */}
              <div
                className={`
                  max-w-[70%] px-3 py-2 text-sm rounded-xl
                  ${isUser ? "bg-[#2E2E2E]" : "bg-[#1E1E1E]"}
                `}
              >
                {msg.text}
              </div>

              {/* User Icon */}
              {isUser && (
                <span className="text-xl select-none">👤</span>
              )}
            </div>
          );
        })}

        <div ref={bottomRef} />
      </div>

      {/* INPUT BAR */}
      <div className="p-4 border-t border-[#2E2E2E] bg-[#1A1A1A]">
        <div className="
          w-full flex items-center gap-3 px-4 py-3
          bg-[#2F2F2F] rounded-3xl shadow-lg
        ">
          
          {/* Attach Button */}
          <FiPlus className="text-white text-xl cursor-pointer opacity-70 hover:opacity-100" />

          {/* Text Input */}
          <input
            className="
              flex-1 bg-transparent text-[#EAEAEA] text-sm
              outline-none placeholder-[#9E9E9E]
            "
            placeholder="Ask anything..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && sendMessage()}
          />

          {/* Mic */}
          <FiMic className="text-white text-lg cursor-pointer opacity-70 hover:opacity-100" />

          {/* Send Button */}
          <button
            onClick={sendMessage}
            className="
              w-8 h-8 bg-white flex items-center justify-center 
              rounded-full shadow-md hover:scale-105 transition
            "
          >
            <RxPaperPlane className="text-black text-sm" />
          </button>

        </div>
      </div>

    </div>
  );
}
