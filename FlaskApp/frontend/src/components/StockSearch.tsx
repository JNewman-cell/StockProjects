import React, { useState } from 'react';
import { 
  TextField,
  Button,
  Box,
  Typography,
  Autocomplete,
  Card,
  CardContent,
  CircularProgress
} from '@mui/material';
import axios from 'axios';

interface StockSearchProps {}

const StockSearch: React.FC<StockSearchProps> = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [stockData, setStockData] = useState<any>(null);

  const handleSearch = async () => {
    try {
      const response = await axios.get(`/api/stock/${selectedStock || searchQuery}`);
      setStockData(response.data);
    } catch (error) {
      console.error('Error fetching stock data:', error);
    }
  };

  const handleInputChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchQuery(value);

    if (value.length >= 2) {
      try {
        const response = await axios.get(`/api/suggestions/${value}`);
        setSuggestions(response.data);
      } catch (error) {
        console.error('Error fetching suggestions:', error);
      }
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Stock Information
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
        <Autocomplete
          freeSolo
          options={suggestions}
          value={selectedStock}
          onChange={(event, newValue) => setSelectedStock(newValue)}
          onInputChange={(event, newValue) => setSearchQuery(newValue)}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Search Stock"
              variant="outlined"
              onChange={handleInputChange}
              fullWidth
            />
          )}
          sx={{ width: 300 }}
        />
        <Button 
          variant="contained" 
          onClick={handleSearch}
          disabled={!searchQuery && !selectedStock}
        >
          Search
        </Button>
      </Box>

      {stockData && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {stockData.symbol}
            </Typography>
            {/* Add more stock data display here */}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default StockSearch;
