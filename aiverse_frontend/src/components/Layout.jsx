import Navbar from './Navbar';
import Footer from './Footer';

export default function Layout({ children, showFooter = true }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-16">
        {children}
      </main>
      {showFooter && <Footer />}
    </div>
  );
}