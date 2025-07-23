import { useEffect } from "react";
import { useAuth } from "react-oidc-context";
import { useNavigate } from "react-router";
import { Box, Text } from "@chakra-ui/react";

export const OAuthCallback = () => {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        if (auth.isLoading) {
          return; // Wait for auth to finish loading
        }

        if (auth.isAuthenticated) {
          // User is authenticated, redirect to home
          navigate("/", { replace: true });
        } else {
          // Authentication failed, redirect to login
          navigate("/login", { replace: true });
        }
      } catch (error) {
        console.error("OAuth callback error:", error);
        navigate("/login", { replace: true });
      }
    };

    handleCallback();
  }, [auth.isAuthenticated, auth.isLoading, navigate]);

  return (
    <Box
      height="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      flexDirection="column"
      gap={4}
    >
      <Text fontSize="lg">Processing authentication...</Text>
      <Text fontSize="sm" color="gray.500">
        Please wait while we complete your login.
      </Text>
    </Box>
  );
};