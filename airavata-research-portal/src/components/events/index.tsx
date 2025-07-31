import {Accordion, Container, Spacer, Span} from "@chakra-ui/react";
import {Apr11Workshop} from "./Apr11Workshop";
import {May7Workshop} from "./May7Workshop";
import {Jul28AllenWorkshop} from "@/components/events/Jul28AllenWorkshop.tsx";

export const Events = () => {
  return (
      <Container maxW="breakpoint-lg" my={8}>
        <Accordion.Root multiple defaultValue={[events[0].id]}>
          {events.map((event) => (
              <Accordion.Item key={event.id} value={event.id} mb={8}>
                <Accordion.ItemTrigger _hover={{cursor: 'pointer', bg: 'gray.100'}}>
                  {event.name} <Spacer/>
                  <Span color="gray.400" fontSize="sm">
                    {event.id}
                  </Span>
                  <Accordion.ItemIndicator/>
                </Accordion.ItemTrigger>

                <Accordion.ItemContent>
                  <Accordion.ItemBody>{event.component()}</Accordion.ItemBody>
                </Accordion.ItemContent>
              </Accordion.Item>
          ))}
        </Accordion.Root>
      </Container>
  );
};

const events = [
  {
    id: "July 28-30, 2025",
    name: "2025 Allen Institute Modeling Software Workshop (28-30 July 2025)",
    component: Jul28AllenWorkshop
  },
  {
    id: "May 7, 2025",
    name: "Cyberinfrastructure and Services for Science & Engineering Workshop",
    component: May7Workshop,
  },
  {
    id: "April 11, 2025",
    name: "Data-Driven and Large-Scale Modeling in Neuroscience",
    component: Apr11Workshop,
  }
];
