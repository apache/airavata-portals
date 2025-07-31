import {Heading, VStack} from "@chakra-ui/react";
import {KeyPair} from "../typography/KeyPair";

export const Jul28AllenWorkshop = () => {
  return (
      <>
        <Heading fontSize="3xl" lineHeight={1.2}>
          2025 Allen Institute Modeling Software Workshop (July 28-30, 2025)
        </Heading>
        <VStack gap={1} align="start" mt={2}>
          <KeyPair
              keyStr="Workshop Details"
              valueStr="https://alleninstitute.org/events/2025-modeling-software-workshop"
              href="https://alleninstitute.org/events/2025-modeling-software-workshop"
          />
          <KeyPair
              keyStr="User Instructions"
              valueStr="Cybershuttle Instructions for Allen Workshop"
              href="https://drive.google.com/file/d/1tb3U8dKL4Jq_K-l45X6w7CgBE0To0Fmu/view?usp=sharing"
          />
          <KeyPair
              keyStr="FAQ"
              valueStr="Cybershuttle FAQ"
              href="https://drive.google.com/file/d/1IQIqWUwN_gONCilEW7KWxsVa4b7iNuoy/view?usp=sharing"
          />
        </VStack>
      </>
  );
};
