import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const userId = params.get("user_id");
    if (token) localStorage.setItem("clipstream_token", token);
    if (userId) localStorage.setItem("clipstream_user_id", userId);
    // Redirect to home or dashboard
    navigate("/");
  }, [navigate]);

  return <div>Authenticating...</div>;
}
