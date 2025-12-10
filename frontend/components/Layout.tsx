import React from "react";

type Props = {
  children: React.ReactNode;
};

export default function Layout({ children }: Props) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-sky-50 to-indigo-50 flex items-start py-12">
      <div className="w-full max-w-3xl mx-auto px-6">
        <header className="mb-8 text-center">
          <div className="inline-flex items-center gap-3 bg-white/60 backdrop-blur rounded-full px-4 py-2 shadow">
            <svg
              className="w-8 h-8 text-indigo-600"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden
            >
              <path
                d="M12 2C8 2 5 5 5 9c0 6 7 11 7 11s7-5 7-11c0-4-3-7-7-7z"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="12" cy="9" r="2.2" fill="currentColor" />
            </svg>
            <div className="text-left">
              <h1 className="text-2xl font-semibold text-gray-800">
                Pickabook
              </h1>
              <p className="text-sm text-gray-600">
                Personalize a children's-book style illustration
              </p>
            </div>
          </div>
        </header>

        <main>
          <div className="bg-white rounded-2xl shadow-xl p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
