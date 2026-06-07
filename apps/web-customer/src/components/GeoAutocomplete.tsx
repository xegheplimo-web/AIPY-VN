import { useState, useEffect, useRef } from 'react';
import { Search, MapPin, X } from 'lucide-react';
import { cn } from '../lib/utils';

interface Suggestion {
  id: string;
  name: string;
  address: string;
  category_icon?: string;
  distance?: string;
}

interface GeoAutocompleteProps {
  onSearch: (query: string) => void;
  onSuggestionSelect?: (suggestion: Suggestion) => void;
  placeholder?: string;
  className?: string;
  location?: { lat: number; lng: number };
}

export default function GeoAutocomplete({
  onSearch,
  onSuggestionSelect,
  placeholder = 'Tìm kiếm cửa hàng, sản phẩm...',
  className,
  location,
}: GeoAutocompleteProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 2) {
        setLoading(true);
        try {
          const response = await fetch(
            `/api/geo/autocomplete?q=${encodeURIComponent(query)}${location ? `&lat=${location.lat}&lng=${location.lng}` : ''}`
          );
          const data = await response.json();
          setSuggestions(data.suggestions || []);
          setShowSuggestions(true);
        } catch (error) {
          console.error('Search error:', error);
          setSuggestions([]);
        } finally {
          setLoading(false);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, location]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const handleSuggestionClick = (suggestion: Suggestion) => {
    setQuery(suggestion.name);
    setShowSuggestions(false);
    onSuggestionSelect?.(suggestion);
  };

  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
      setShowSuggestions(false);
    }
  };

  return (
    <div className={cn('relative w-full', className)}>
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={() => query.length >= 2 && setShowSuggestions(true)}
            placeholder={placeholder}
            className={cn(
              'w-full pl-10 pr-10 py-3 rounded-lg border border-gray-300',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'transition-all duration-200',
              'placeholder:text-gray-400'
            )}
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </form>

      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-2 bg-white rounded-lg shadow-lg border border-gray-200 max-h-96 overflow-y-auto"
        >
          {loading ? (
            <div className="p-4 text-center text-gray-500">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            suggestions.map((suggestion) => (
              <button
                key={suggestion.id}
                type="button"
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0"
              >
                <div className="flex items-start gap-3">
                  {suggestion.category_icon && (
                    <span className="text-2xl mt-0.5">{suggestion.category_icon}</span>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">{suggestion.name}</div>
                    <div className="text-sm text-gray-600 truncate mt-1">{suggestion.address}</div>
                    {suggestion.distance && (
                      <div className="text-sm text-blue-600 mt-1">{suggestion.distance}</div>
                    )}
                  </div>
                  <MapPin className="h-5 w-5 text-gray-400 flex-shrink-0 mt-1" />
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
