import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Send, Bot, User, BookOpen, ShieldAlert,
  LogOut, Scale, Sparkles, ShieldCheck
} from "lucide-react";
import { API_BASE_URL } from "../api/axiosClient";

export default function ChatPage() {
  const navigate = useNavigate();
  const userInfo = JSON.parse(localStorage.getItem("user_info") || "{}");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Xin chào! Tôi là Trợ lý AI Pháp lý nội bộ. Bạn có thể đặt câu hỏi về Luật Doanh nghiệp, Bộ luật Lao động, Hợp đồng... Mọi thông tin cá nhân nhạy cảm (CCCD, SĐT, Email) sẽ được tự động ẩn danh trước khi xử lý.",
      citations: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_info");
    navigate("/login");
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userQuestion = input.trim();
    setInput("");
    setIsStreaming(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userQuestion },
      { role: "assistant", content: "", citations: [], sanitizedQuery: "" },
    ]);

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question: userQuestion }),
      });

      if (!response.ok) {
        const errData = await response.json();
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: errData.detail || "Yêu cầu bị từ chối bởi bộ lọc an toàn.",
            isError: true,
            citations: [],
          };
          return updated;
        });
        setIsStreaming(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.replace("data: ", "").trim();
            if (!jsonStr) continue;

            const parsed = JSON.parse(jsonStr);
            if (parsed.type === "meta") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1].citations = parsed.citations || [];
                updated[updated.length - 1].sanitizedQuery = parsed.sanitized_query || "";
                return updated;
              });
            } else if (parsed.type === "token") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1].content += parsed.content;
                return updated;
              });
            }
          }
        }
      }
    } catch (error) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "⚠️ Lỗi kết nối đến Back-end RAG Server. Hãy kiểm tra Uvicorn cổng 8000.",
          isError: true,
          citations: [],
        };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-100">
      <aside className="w-72 bg-slate-900 text-white flex flex-col justify-between p-4 hidden md:flex">
        <div>
          <div className="flex items-center gap-3 px-2 py-3 border-b border-slate-800">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Scale size={22} />
            </div>
            <div>
              <h2 className="font-bold text-sm">Private AI Cloud</h2>
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                <span className="w-2 h-2 bg-emerald-400 rounded-full inline-block"></span>
                On-Premise RAG Active
              </span>
            </div>
          </div>

          <div className="mt-6">
            <p className="text-xs uppercase text-slate-400 font-semibold px-2 mb-2">
              Gợi ý câu hỏi pháp lý
            </p>
            <div className="space-y-2 text-sm">
              {[
                "Điều kiện thành lập công ty TNHH 1 thành viên là gì?",
                "Thời giờ làm việc bình thường của người lao động?",
                "Tôi là Nguyễn Văn A, CCCD 001200012345 muốn hỏi về hợp đồng lao động.",
              ].map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(sample)}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 text-xs transition line-clamp-2"
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-4">
          <div className="flex items-center justify-between px-2">
            <div>
              <p className="text-sm font-medium">{userInfo.full_name || "Người dùng"}</p>
              <p className="text-xs text-slate-400 capitalize">
                Vai trò: {userInfo.role || "user"}
              </p>
            </div>
            <button
              onClick={handleLogout}
              title="Đăng xuất"
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="text-blue-600" size={20} />
            <h1 className="font-semibold text-slate-800">
              Trợ lý Tra cứu Pháp luật Doanh nghiệp (RAG Streaming)
            </h1>
          </div>
          <button
            onClick={handleLogout}
            className="md:hidden text-sm text-slate-600 hover:text-red-600 flex items-center gap-1"
          >
            <LogOut size={16} /> Thoát
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 max-w-4xl mx-auto ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${
                    msg.isError ? "bg-red-100 text-red-600" : "bg-blue-600 text-white"
                  }`}
                >
                  {msg.isError ? <ShieldAlert size={20} /> : <Bot size={20} />}
                </div>
              )}

              <div
                className={`rounded-2xl px-5 py-3.5 max-w-2xl shadow-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : msg.isError
                    ? "bg-red-50 border border-red-200 text-red-800"
                    : "bg-white border border-slate-200 text-slate-800"
                }`}
              >
                {msg.sanitizedQuery && msg.sanitizedQuery.includes("_HIDDEN]") && (
                  <div className="mb-2 px-2.5 py-1 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800 flex items-center gap-1.5">
                    <ShieldCheck size={14} className="shrink-0" />
                    <span>Đã ẩn dữ liệu nhạy cảm: {msg.sanitizedQuery}</span>
                  </div>
                )}

                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content || (isStreaming && index === messages.length - 1 ? "Đang suy luận..." : "")}
                </div>

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <p className="text-xs font-semibold text-slate-500 flex items-center gap-1.5 mb-2">
                      <BookOpen size={14} className="text-blue-600" />
                      Nguồn trích dẫn pháp lý ({msg.citations.length}):
                    </p>
                    <div className="space-y-2">
                      {msg.citations.map((cite, cIdx) => (
                        <div
                          key={cIdx}
                          className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                        >
                          <div className="flex justify-between font-medium text-blue-700 mb-1">
                            <span>📄 {cite.source_file} (Đoạn #{cite.chunk_id})</span>
                            <span>Độ khớp: {(cite.score * 100).toFixed(1)}%</span>
                          </div>
                          <p className="text-slate-600 line-clamp-3">{cite.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-9 h-9 rounded-full bg-slate-700 text-white flex items-center justify-center shrink-0">
                  <User size={18} />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="bg-white border-t border-slate-200 p-4">
          <form
            onSubmit={handleSendMessage}
            className="max-w-4xl mx-auto flex items-center gap-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isStreaming}
              placeholder="Nhập câu hỏi pháp lý của bạn (Ví dụ: Điều kiện thành lập công ty TNHH)..."
              className="flex-1 border border-slate-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-slate-50"
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 rounded-xl font-medium text-sm flex items-center gap-2 transition disabled:opacity-50"
            >
              <Send size={18} />
              <span>Gửi</span>
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}