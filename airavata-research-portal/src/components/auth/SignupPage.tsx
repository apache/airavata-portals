import { Box, Button, Container, HStack, Input, Text, VStack } from "@chakra-ui/react";
import { useState } from "react";
import { useAuth } from "react-oidc-context";
import { useNavigate } from "react-router";

// Using the existing hero image
import HeroImage from "../../assets/Hero.original.png";

export const Signup = () => {
  const [loading, setLoading] = useState(false);
  const auth = useAuth();
  const navigate = useNavigate();

  const redirect = new URLSearchParams(window.location.search).get("redirect") || "/";

  const handleSignup = () => {
    setLoading(true);
    auth.signinRedirect({
      redirect_uri: `${window.location.origin}${redirect}`,
      extraQueryParams: {
        prompt: "login",
        kc_idp_hint: "oidc",
      },
    });
  };

  return (
    <Container maxWidth="100vw" height="100vh" padding={0}>
      <HStack height="100vh" gap={0}>
        {/* Left side - Hero Image */}
        <Box 
          width="50%" 
          height="100vh" 
          position="relative"
          backgroundImage={`url(${HeroImage})`}
          backgroundSize="cover"
          backgroundPosition="center"
        >
          <Box
            position="absolute"
            bottom="8"
            left="8"
            color="white"
          >
            <HStack gap={2} marginBottom={2}>
              <Box
                width="20px"
                height="20px"
                borderRadius="md"
                backgroundColor="rgba(255,255,255,0.2)"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text fontSize="xs" color="white">🏠</Text>
              </Box>
              <Text fontSize="sm" color="white">Home</Text>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold" lineHeight="1.2">
              Your Gateway to Seamless
              <br />
              Scientific Computing
            </Text>
          </Box>
        </Box>

        {/* Right side - Signup Form */}
        <Box width="50%" height="100vh" display="flex" flexDirection="column">
          {/* Header */}
          <HStack justifyContent="space-between" padding={6}>
            <HStack gap={2}>
              <Box
                width="24px"
                height="24px"
                backgroundColor="blue.500"
                borderRadius="sm"
              />
              <Text fontWeight="bold" color="blue.500">Cybershuttle</Text>
            </HStack>
          </HStack>

          {/* Signup Form */}
          <VStack 
            flex={1} 
            justifyContent="center" 
            padding={8}
            maxWidth="400px"
            margin="0 auto"
            gap={6}
          >
            <VStack gap={2} alignItems="flex-start" width="100%">
              <Text fontSize="2xl" fontWeight="bold">Create Account</Text>
              <Text color="gray.500" fontSize="sm">
                Let your passion fuel your drive as you research through top
                scientific discoveries
              </Text>
            </VStack>

            <VStack gap={4} width="100%">
              <HStack gap={4} width="100%">
                <Input placeholder="First Name" backgroundColor="gray.50" border="none" />
                <Input placeholder="Last Name" backgroundColor="gray.50" border="none" />
              </HStack>
              <Input placeholder="Username" backgroundColor="gray.50" border="none" />
              <Input placeholder="E-mail" backgroundColor="gray.50" border="none" />
              <Input placeholder="Password" type="password" backgroundColor="gray.50" border="none" />
              <Input placeholder="Confirm Password" type="password" backgroundColor="gray.50" border="none" />
            </VStack>

            <VStack gap={3} width="100%">
              <Button
                width="100%"
                backgroundColor="blue.400"
                color="white"
                _hover={{ backgroundColor: "blue.500" }}
                onClick={handleSignup}
                loading={loading}
              >
                Sign Up
              </Button>

              <Text fontSize="sm" color="gray.400">or</Text>

              <Button
                width="100%"
                variant="outline"
                borderColor="gray.200"
                backgroundColor="white"
                _hover={{ backgroundColor: "gray.50" }}
                leftIcon={<Text>🔗</Text>}
                onClick={handleSignup}
                loading={loading}
              >
                Sign up with Cilogon
              </Button>

              <Text fontSize="sm" color="gray.600" textAlign="center">
                Already have an account?{" "}
                <Text 
                  as="span" 
                  color="blue.500" 
                  cursor="pointer"
                  onClick={() => navigate("/login")}
                >
                  Sign In
                </Text>
              </Text>
            </VStack>
          </VStack>

          {/* Footer */}
          <Text fontSize="xs" color="gray.400" textAlign="center" padding={4}>
            © 2024 Cybershuttle - MIT Sugessie
          </Text>
        </Box>
      </HStack>
    </Container>
  );
};