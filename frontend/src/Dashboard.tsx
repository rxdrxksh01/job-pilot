import { useEffect, useState } from 'react';
import { useSupabase } from './useSupabase';
import { useUser } from '@clerk/clerk-react';
import { ExternalLink, MapPin, Search, Loader2 } from 'lucide-react';

export default function Dashboard() {
  const supabase = useSupabase();
  const { user } = useUser();
  const [jobs, setJobs] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('India');
  const [activeLocation, setActiveLocation] = useState('India');
  const [hasSearched, setHasSearched] = useState(false);

  const fetchJobs = async () => {
    const { data, error } = await supabase
      .from('jobs')
      .select('*')
      .order('scraped_at', { ascending: false });

    if (!error) {
      setJobs(data || []);
      if (data && data.length > 0) setHasSearched(true);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Check for new jobs every 5s
    return () => clearInterval(interval);
  }, [supabase]);

  const handleSearch = async () => {
    if (!searchQuery.trim() || !user) return;
    
    setSearching(true);
    setJobs([]); // Clear results immediately
    setHasSearched(true);
    setActiveLocation(location); 

    // Dynamic API URL: Use localhost if on local, otherwise use Render URL
    const API_URL = window.location.hostname === 'localhost' 
      ? 'http://localhost:8000' 
      : 'https://job-pilot-8yvz.onrender.com'; 

    try {
      await fetch(`${API_URL}/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          location: location,
          user_id: user.id
        }),
      });
    } catch (err) {
      console.error('Search failed:', err);
    }
    setTimeout(() => setSearching(false), 3000);
  };

  return (
    <div className="w-full flex flex-col gap-8">
      {/* SEARCH BAR */}
      <div className="w-full bg-white p-6 rounded-3xl shadow-2xl shadow-blue-100/50 border border-slate-100 flex flex-col md:flex-row gap-4 items-center">
        <div className="flex-1 flex items-center bg-slate-50 rounded-xl px-4 py-2 border border-slate-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition-all">
          <Search className="text-slate-400 mr-2 h-5 w-5" />
          <input
            type="text"
            placeholder="Search for jobs (e.g. Machine Learning, Software Engineer)"
            className="w-full bg-transparent border-none focus:outline-none text-slate-700"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>

        <button
          onClick={handleSearch}
          disabled={searching}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold flex items-center transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-200"
        >
          {searching ? (
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
          ) : (
            <Search className="h-5 w-5 mr-2" />
          )}
          Search
        </button>
      </div>

      {hasSearched && (
        <div className="w-full bg-white p-8 rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Results for "{activeLocation}"</h2>
            <div className="text-sm font-medium text-slate-400 bg-slate-50 px-4 py-1.5 rounded-full">
              {jobs.length} jobs found
            </div>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-100">
            <table className="w-full text-sm text-left text-slate-600">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100">
                <tr>
                  <th scope="col" className="px-6 py-4 font-semibold">Company</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Job Title</th>
                  <th scope="col" className="px-6 py-4 font-semibold text-center">LinkedIn</th>
                  <th scope="col" className="px-6 py-4 font-semibold">AI Match</th>
                </tr>
              </thead>
              <tbody>
                {jobs.length === 0 && !searching && (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-slate-400">
                      Searching for live jobs... Please wait.
                    </td>
                  </tr>
                )}
                {jobs.map((job) => (
                  <tr key={job.job_id} className="border-b border-slate-50 hover:bg-blue-50/20 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">{job.company}</td>
                    <td className="px-6 py-4">{job.job_title}</td>
                    <td className="px-6 py-4 text-center">
                      <a href={`https://www.linkedin.com/jobs/view/${job.job_id}/`} target="_blank" className="text-blue-600 hover:underline font-medium inline-flex items-center gap-1">
                        Post <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </td>
                    <td className="px-6 py-4">
                      {job.resume_score ? (
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${job.resume_score >= 80 ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                          {job.resume_score}%
                        </span>
                      ) : 'Pending'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

