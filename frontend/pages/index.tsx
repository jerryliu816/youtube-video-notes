import { useUser } from "@auth0/nextjs-auth0/client";
import { useState } from "react";
import axios from "axios";

export default function Home() {
  const { user, error, isLoading } = useUser();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [language, setLanguage] = useState("en");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const summarizeVideo = async () => {
    if (!user) {
      setErrorMessage("You must be logged in to access this feature.");
      console.warn("Unauthorized user tried to access summarization.");
      return;
    }

    setLoading(true);
    setSummary("");
    setErrorMessage("");

    try {
      console.info(`Requesting summary for ${youtubeUrl} in ${language} by user ${user.email}`);

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_FASTAPI_BACKEND}/summarize/`,
        {
          youtube_url: youtubeUrl,
          target_language: language,
          mode: "video",
          user_email: user.email, // Pass user email to the backend
        }
      );

      console.info("Summary received:", response.data);
      setSummary(response.data.summary);
    } catch (error) {
      console.error("API Error:", error);
      setErrorMessage("Failed to fetch summary. Please check the console.");
    } finally {
      setLoading(false);
    }
  };

  return (     
    <>
  <Head>
    <title>Video Notes - Watch Less, Know More</title>
    <meta charSet="UTF-8" />
    <meta name="description" content="Video Notes - Summarizes youtube videos. Get key insights without watching entire video." />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </Head>

    <div className="min-h-screen flex flex-col items-center bg-gray-100">
      <div className="container bg-white shadow-lg rounded-lg p-8 mt-10">
        <h1 className="text-3xl font-bold text-center text-blue-600">
          🎬 YouTube Video Notes
        </h1>

        {isLoading && <p className="text-gray-500 text-center">Loading...</p>}
        {error && <p className="text-red-500 text-center">{error.message}</p>}

        {user ? (
          <>
            <p className="text-lg text-center text-gray-700 mt-4">
              Welcome, <span className="font-bold">{user.name}</span>!
            </p>
            <div className="flex justify-center mt-4">
              <a
                href="/api/auth/logout"
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Logout
              </a>
            </div>

            <div className="mt-6">
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="Enter YouTube URL"
                className="w-full p-3 border rounded-md"
              />
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full p-3 border rounded-md mt-3"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
              <button
                onClick={summarizeVideo}
                disabled={loading}
                className="w-full mt-4 bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
              >
                {loading ? "Generates Video Notes..." : "Get Video Note"}
              </button>
            </div>

            {errorMessage && <p className="text-red-500 mt-4">{errorMessage}</p>}

            {summary && (
              <div className="mt-8 p-4 bg-gray-200 rounded-lg shadow">
                <h2 className="text-xl font-semibold text-gray-700">
                  📌 Summary:
                </h2>
                <p className="text-gray-800 whitespace-pre-line mt-2 leading-relaxed">
                  {summary}
                </p>
              </div>
            )}
          </>
        ) : (
          <>
            <p className="text-lg text-center text-gray-700 mt-4">
              Please log in with your Google account to use Video Notes.
            </p>
            <div className="flex justify-center mt-4">
              <a
                href="/api/auth/login"
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                Login
              </a>
            </div>
          </>
        )}
      </div>
    </div>
    </>
  );
}
