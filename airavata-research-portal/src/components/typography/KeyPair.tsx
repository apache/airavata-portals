import {Link, Text} from "@chakra-ui/react";

export const KeyPair = ({
                          keyStr,
                          valueStr,
                          href
                        }: {
  keyStr: string;
  valueStr: string;
  href?: string;
}) => {
  const isLink = valueStr.startsWith("http") || (href != null);
  return (
      <Text>
        <Text as="span" fontWeight="bold">
          {keyStr}:{" "}
        </Text>

        {isLink ? (
            <Link
                href={href}
                target="_blank"
                color="blue.600"
                fontWeight="normal"
            >
              {valueStr}
            </Link>
        ) : (
            <Text as="span" fontWeight="normal">
              {valueStr}
            </Text>
        )}
      </Text>
  );
};
