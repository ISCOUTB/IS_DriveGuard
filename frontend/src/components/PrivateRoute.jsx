import { Navigate } from "react-router-dom";
import { isAuthenticated } from "../services/api";

export default function PrivateRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
