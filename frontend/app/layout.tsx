import type { Metadata } from 'next';
import { HamburgerMenu } from '../components/hamburger-menu';
import './globals.css';

export const metadata: Metadata = {
  title: 'InsightAI Interview',
  description: 'Rio Biscuits Market Research Interview',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <HamburgerMenu />
        {children}
      </body>
    </html>
  );
}