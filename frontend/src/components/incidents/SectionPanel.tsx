import type { ReactNode } from "react";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";

export function SectionPanel({
  id,
  title,
  description,
  action,
  children,
  className,
}: {
  id?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} aria-labelledby={id ? `${id}-title` : undefined} className={className}>
      <Card>
        <CardHeader
          title={<span id={id ? `${id}-title` : undefined}>{title}</span>}
          description={description}
          action={action}
        />
        <CardBody>{children}</CardBody>
      </Card>
    </section>
  );
}