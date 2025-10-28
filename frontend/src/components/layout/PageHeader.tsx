interface PageHeaderProps {
  title: string;
  subtitle: string;
  actions?: React.ReactNode;
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h1 className="font-crimson font-bold text-4xl leading-tight text-[#333333] dark:text-foreground">
          {title}
        </h1>
        <p className="font-crimson font-normal text-base leading-relaxed text-figma-muted dark:text-muted-foreground mt-1">
          {subtitle}
        </p>
      </div>
      {actions && <div className="flex items-start gap-2">{actions}</div>}
    </div>
  );
}
