import "./globals.css";

export const metadata = {
  title: "Room Boundary Scanner",
  description: "Local-only ARCore room scanning control room",
};

export const viewport = {
  themeColor: "#f4f1ea",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
