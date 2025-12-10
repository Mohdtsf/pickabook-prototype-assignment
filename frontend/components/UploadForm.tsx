import { useState, useRef, useCallback } from "react";
import axios from "axios";
import { BACKEND } from "../lib/config";

export default function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setErrorMsg(null);
    setFile(f);
    if (f) setPreview(URL.createObjectURL(f));
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0] ?? null;
    if (f && f.type.startsWith("image/")) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
    } else {
      setErrorMsg("Please drop a valid image file.");
    }
  }, []);

  async function upload() {
    if (!file) return setErrorMsg("Please choose a photo to personalize.");
    const fd = new FormData();
    fd.append("photo", file);
    setStatus("uploading");
    setErrorMsg(null);
    try {
      const res = await axios.post(`${BACKEND}/upload`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setTaskId(res.data.task_id);
      setStatus("processing");
      pollStatus(res.data.task_id);
    } catch (err: any) {
      console.error(err);
      setStatus("error");
      setErrorMsg(err?.message || "Upload failed");
    }
  }

  async function pollStatus(id: string) {
    try {
      const r = await axios.get(`${BACKEND}/status/${id}`);
      if (r.data.status === "done") {
        setStatus("done");
        const maybeUrl = r.data.result_url || r.data.stylized_url;
        if (maybeUrl) {
          setResultUrl(
            maybeUrl.startsWith("http") ? maybeUrl : `${BACKEND}${maybeUrl}`
          );
        }
      } else if (r.data.status === "error") {
        setStatus("error");
        setErrorMsg(r.data.error || "Processing failed");
      } else {
        setTimeout(() => pollStatus(id), 1500);
      }
    } catch (err: any) {
      console.error(err);
      setStatus("error");
      setErrorMsg(err?.message || "Status check failed");
    }
  }

  const openResult = () => {
    if (!resultUrl) return;
    const url = resultUrl.startsWith("http")
      ? resultUrl
      : `${BACKEND}${resultUrl}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const downloadResult = async () => {
    if (!resultUrl) return;
    try {
      setStatus("downloading");
      const url = resultUrl.startsWith("http")
        ? resultUrl
        : `${BACKEND}${resultUrl}`;
      const res = await axios.get(url, { responseType: "blob" });
      const blob = new Blob([res.data], { type: res.data.type || "image/png" });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      const parts = url.split("/");
      link.download = parts[parts.length - 1] || "result.png";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      setStatus("done");
    } catch (err) {
      console.error(err);
      setErrorMsg("Download failed");
      setStatus("error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">
            Create your personalized illustration
          </h2>
          <p className="text-sm text-gray-500">
            Upload a photo and we’ll transform the face into a charming
            children&apos;s-book style.
          </p>
        </div>
        <div className="text-sm text-gray-500">
          Status: <span className="font-medium">{status ?? "idle"}</span>
        </div>
      </div>

      {!preview && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          className={`border-2 ${
            dragOver
              ? "border-indigo-400 bg-indigo-50/40"
              : "border-dashed border-gray-200"
          } rounded-lg p-6 flex flex-col items-center justify-center text-center transition`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={onFileChange}
            className="hidden"
          />
          <div className="max-w-md">
            <svg
              className="mx-auto h-12 w-12 text-indigo-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16l5-5 5 5M12 11v10"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              Drag & drop an image here, or{" "}
              <button
                onClick={() => inputRef.current?.click()}
                className="text-indigo-600 font-medium"
              >
                browse
              </button>
            </p>
            <p className="mt-1 text-xs text-gray-400">
              We recommend a clear frontal face photo for best results.
            </p>
          </div>
        </div>
      )}

      {preview && (
        <div className="flex items-start gap-4">
          <div className="w-36 h-36 rounded-lg overflow-hidden border">
            <img
              src={preview}
              alt="preview"
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex-1">
            <div className="flex gap-3">
              <button
                onClick={upload}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg shadow hover:shadow-lg"
              >
                Personalize
              </button>
              <button
                onClick={() => {
                  setFile(null);
                  setPreview(null);
                  setResultUrl(null);
                  setStatus(null);
                }}
                className="px-4 py-2 border rounded-lg"
              >
                Reset
              </button>
            </div>
            <div className="mt-3 text-sm text-gray-500">
              Selected file: <span className="font-medium">{file?.name}</span>
            </div>
          </div>
        </div>
      )}

      {errorMsg && <div className="text-sm text-red-600">{errorMsg}</div>}

      {status === "uploading" || status === "processing" ? (
        <div className="flex items-center gap-3">
          <svg
            className="animate-spin h-6 w-6 text-indigo-600"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
          <div className="text-sm text-gray-600">
            Working on it — this may take a few seconds.
          </div>
        </div>
      ) : null}

      {resultUrl && (
        <div className="mt-4 border rounded-lg p-4 bg-gray-50">
          <div className="text-sm text-gray-600">Result</div>
          <div className="mt-3 flex flex-col items-center">
            <img
              src={resultUrl}
              alt="result"
              className="rounded-lg shadow-md max-w-full"
            />
            <div className="mt-3 flex gap-3">
              <button
                onClick={openResult}
                className="px-4 py-2 bg-white border rounded-lg"
              >
                Open
              </button>
              <button
                onClick={downloadResult}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg"
              >
                Download
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
