import React from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import StockSearch from './components/StockSearch';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <StockSearch />
      </Container>
    </ThemeProvider>
  );
}

export default App;
