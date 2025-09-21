import { useState, useEffect, useCallback } from 'react';
import {
  Upload,
  FileText,
  Database,
  Code,
  Layers,
  BarChart3,
  CheckCircle,
  AlertTriangle,
  Info,
  Download,
  Play,
  Eye,
  Zap,
  Settings,
  Cpu,
  HardDrive,
  Activity,
  XCircle,
  Clock,
  Users,
  TrendingUp,
  Shield,
  Globe,
  Server,
  Monitor,
  FileJson,
  Table
} from 'lucide-react';

const API_BASE = '/api/v1';

// Utility functions
const formatBytes = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const downloadFile = (content, filename, mimeType = 'text/plain') => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

const downloadJSON = (data, filename) => {
  const jsonString = JSON.stringify(data, null, 2);
  downloadFile(jsonString, filename, 'application/json');
};

// API helper functions
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to backend server. Please ensure the server is running.');
    }
    throw error;
  }
};

const uploadFile = async (file, targetDb, tableName, exportFormat) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_db', targetDb);
  formData.append('table_name', tableName);
  formData.append('export_format', exportFormat);

  const response = await fetch(`${API_BASE}/modernize`, {
    method: 'POST',
    body: formData,
    // Don't set Content-Type header - let browser set it with boundary for FormData
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `Upload failed: ${response.statusText}`);
  }

  return await response.json();
};

const exportFileAsJSON = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/export/json`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `Export failed: ${response.statusText}`);
  }

  return await response.json();
};

// Components
const MetricCard = ({ icon: Icon, title, value, subtitle, trend, variant = 'primary', className = '' }) => (
  <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
    <div className="flex items-center justify-between">
      <div>
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">{title}</h3>
        <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        {subtitle && <p className="mt-1 text-sm text-gray-600">{subtitle}</p>}
      </div>
      <div className={`text-2xl ${
        variant === 'primary' ? 'text-blue-500' :
        variant === 'success' ? 'text-green-500' :
        variant === 'warning' ? 'text-yellow-500' :
        variant === 'error' ? 'text-red-500' : 'text-gray-500'
      }`}>
        <Icon size={32} />
      </div>
    </div>
    {trend && (
      <div className="mt-4 flex items-center text-sm">
        {trend > 0 ? (
          <span className="text-green-600 flex items-center">
            <TrendingUp size={16} className="mr-1" />
            +{trend}%
          </span>
        ) : (
          <span className="text-red-600 flex items-center">
            <TrendingUp size={16} className="mr-1 rotate-180" />
            {trend}%
          </span>
        )}
        <span className="ml-2 text-gray-500">vs baseline</span>
      </div>
    )}
  </div>
);

const StatusBadge = ({ status, children, className = '' }) => {
  const statusClasses = {
    success: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    error: 'bg-red-100 text-red-800 border-red-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200'
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusClasses[status]} ${className}`}>
      {children}
    </span>
  );
};

const LoadingSpinner = ({ size = 24, className = '' }) => (
  <div
    className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${className}`}
    style={{ width: size, height: size }}
  />
);

const FileUploadZone = ({ onFileSelect, selectedFile, loading }) => {
  const handleDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
        loading 
          ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
          : 'border-gray-300 hover:border-gray-400'
      }`}
    >
      <input
        type="file"
        onChange={handleFileInput}
        accept=".csv,.txt,.xlsx,.xls"
        className="hidden"
        id="file-input"
        disabled={loading}
      />
      <label htmlFor="file-input" className="cursor-pointer">
        <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
        
        <div className="space-y-2">
          <p className="text-lg font-medium text-gray-900">
            Drag & drop your file here
          </p>
          <p className="text-sm text-gray-500">
            or click to browse files
          </p>
          <p className="text-xs text-gray-400">
            Supports CSV, TXT (including AS/400 fixed-width), XLSX, XLS files up to 50MB
          </p>
        </div>
      </label>

      {selectedFile && (
        <div className="mt-4 p-3 bg-gray-100 rounded-lg">
          <div className="flex items-center justify-center space-x-2 text-sm">
            <FileText className="h-4 w-4 text-gray-600" />
            <span className="font-medium">{selectedFile.name}</span>
            <span className="text-gray-500">({formatBytes(selectedFile.size)})</span>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [backendHealth, setBackendHealth] = useState(null);
  const [modernizationResults, setModernizationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [targetDb, setTargetDb] = useState('postgres');
  const [tableName, setTableName] = useState('modernized_table');
  const [exportFormat, setExportFormat] = useState('pandas');
  const [error, setError] = useState(null);
  const [connectionError, setConnectionError] = useState(false);

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const health = await apiCall('/health');
      setBackendHealth(health);
      setConnectionError(false);
      setError(null);
    } catch (err) {
      console.error('Backend health check failed:', err);
      setBackendHealth(null);
      setConnectionError(true);
      setError(err.message);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    
    try {
      const result = await uploadFile(selectedFile, targetDb, tableName, exportFormat);
      setModernizationResults(result);
      setActiveTab('results');
    } catch (err) {
      console.error('Modernization failed:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleJSONExport = async () => {
    if (!selectedFile) return;

    try {
      setLoading(true);
      const result = await exportFileAsJSON(selectedFile);
      const filename = `${selectedFile.name.split('.')[0]}_export.json`;
      downloadJSON(result, filename);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSample = async (sampleType) => {
    try {
      setLoading(true);
      setError(null);
      
      // Get sample data from API
      const sampleData = await apiCall(`/sample-data/${sampleType}`);
      
      // Create a blob from the sample data
      const blob = new Blob([sampleData.data], { type: 'text/csv' });
      const file = new File([blob], `${sampleType}_sample.csv`, { type: 'text/csv' });
      
      setSelectedFile(file);
      setTableName(`${sampleType}_modernized`);
      
      // Process the sample file
      const result = await uploadFile(file, targetDb, `${sampleType}_modernized`, exportFormat);
      setModernizationResults(result);
      setActiveTab('results');
    } catch (err) {
      console.error('Sample processing failed:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-8 text-white">
        <div className="max-w-4xl">
          <h1 className="text-4xl font-bold mb-4">AS/400 Legacy Modernization Assistant</h1>
          <p className="text-xl text-blue-100 leading-relaxed">
            Transform your legacy IBM AS/400 systems into modern, cloud-ready architectures 
            with AI-powered intelligence and automated code generation.
          </p>
        </div>
      </div>

      {/* Backend Status */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Monitor className="h-5 w-5 mr-2 text-gray-600" />
          System Status
        </h2>
        
        {backendHealth ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="flex items-center space-x-3 text-green-600">
              <CheckCircle className="h-6 w-6" />
              <div>
                <p className="font-medium">Backend</p>
                <p className="text-sm opacity-80">Online</p>
              </div>
            </div>
            
            <div className={`flex items-center space-x-3 ${
              backendHealth.ai_enabled ? 'text-blue-600' : 'text-gray-500'
            }`}>
              {backendHealth.ai_enabled ? (
                <Zap className="h-6 w-6" />
              ) : (
                <Settings className="h-6 w-6" />
              )}
              <div>
                <p className="font-medium">AI Processing</p>
                <p className="text-sm opacity-80">
                  {backendHealth.ai_enabled ? 'Enabled' : 'Heuristic Mode'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3 text-green-600">
              <Activity className="h-6 w-6" />
              <div>
                <p className="font-medium">Version</p>
                <p className="text-sm opacity-80">v{backendHealth.version}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3 text-gray-600">
              <Server className="h-6 w-6" />
              <div>
                <p className="font-medium">Environment</p>
                <p className="text-sm opacity-80 capitalize">{backendHealth.environment}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-3 text-red-600">
              <XCircle className="h-6 w-6" />
              <div>
                <p className="font-medium">Backend Connection Failed</p>
                <p className="text-sm opacity-80">
                  {connectionError ? 'Unable to connect to the API server' : 'Server health check failed'}
                </p>
                <div className="mt-2">
                  <code className="text-xs bg-red-100 px-2 py-1 rounded font-mono">
                    Expected API endpoint: {API_BASE}/health
                  </code>
                </div>
                <button 
                  onClick={checkBackendHealth}
                  className="mt-2 text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
          <Zap className="h-12 w-12 text-blue-500 mb-4" />
          <h3 className="text-lg font-semibold mb-2">AI-Powered</h3>
          <p className="text-gray-600 text-sm">
            Smart column mapping and modernization using advanced language models
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
          <Database className="h-12 w-12 text-green-500 mb-4" />
          <h3 className="text-lg font-semibold mb-2">Multi-Database</h3>
          <p className="text-gray-600 text-sm">
            Support for PostgreSQL, MySQL, SQLite, and MongoDB targets
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
          <Layers className="h-12 w-12 text-purple-500 mb-4" />
          <h3 className="text-lg font-semibold mb-2">Microservices</h3>
          <p className="text-gray-600 text-sm">
            Generate modern microservices architecture and deployment configs
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
          <BarChart3 className="h-12 w-12 text-yellow-500 mb-4" />
          <h3 className="text-lg font-semibold mb-2">Quality Analysis</h3>
          <p className="text-gray-600 text-sm">
            Comprehensive data quality assessment and recommendations
          </p>
        </div>
      </div>

      {/* Sample Data Section - Only show if backend is connected */}
      {backendHealth && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-gray-600" />
            Try Sample AS/400 Data
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {['customer', 'employee', 'inventory', 'transactions', 'orders', 'vendors'].map((sampleType) => (
              <button
                key={sampleType}
                onClick={() => loadSample(sampleType)}
                disabled={loading}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <FileText className="h-8 w-8 text-blue-500 mb-2 group-hover:scale-110 transition-transform" />
                <h3 className="font-medium capitalize text-gray-900">{sampleType} Data</h3>
                <p className="text-sm text-gray-600">AS/400 {sampleType} master file</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Connection Instructions */}
      {!backendHealth && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center text-yellow-800">
            <Settings className="h-5 w-5 mr-2" />
            Backend Setup Required
          </h2>
          <div className="space-y-3 text-sm text-yellow-700">
            <p>To use this application, you need to start the FastAPI backend server:</p>
            <div className="bg-yellow-100 p-3 rounded font-mono text-xs">
              <div>1. Install dependencies: pip install -r requirements.txt</div>
              <div>2. Start server: uvicorn main:app --reload --host 0.0.0.0 --port 8000</div>
              <div>3. Ensure server is accessible at: {API_BASE}</div>
            </div>
            <p>Once the server is running, refresh this page or click the "Retry Connection" button above.</p>
          </div>
        </div>
      )}
    </div>
  );

  const renderUpload = () => (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Legacy File Transformation</h1>
        <StatusBadge status={backendHealth ? 'success' : 'error'}>
          {backendHealth ? 'Backend Online' : 'Backend Offline'}
        </StatusBadge>
      </div>

      {!backendHealth && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            <p className="text-red-700 font-medium">Backend server is not accessible</p>
          </div>
          <p className="text-red-600 text-sm mt-1">Please ensure the FastAPI server is running and accessible.</p>
        </div>
      )}
      
      {/* File Upload Section */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-6">Upload Your Legacy File</h2>
        
        <FileUploadZone
          onFileSelect={setSelectedFile}
          selectedFile={selectedFile}
          loading={loading}
        />
        
        {/* Configuration */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Database
            </label>
            <select
              value={targetDb}
              onChange={(e) => setTargetDb(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            >
              <option value="postgres">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
              <option value="mongodb">MongoDB</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Table Name
            </label>
            <input
              type="text"
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="modernized_table"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            >
              <option value="pandas">Standard Processing</option>
              <option value="json">JSON with Metadata</option>
            </select>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="mt-6 flex justify-center space-x-4">
          <button
            onClick={handleFileUpload}
            disabled={!selectedFile || loading || !backendHealth}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 text-base rounded-lg font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
          >
            {loading ? (
              <>
                <LoadingSpinner size={20} className="mr-2" />
                Processing...
              </>
            ) : (
              <>
                <Play className="h-5 w-5 mr-2" />
                Start Modernization
              </>
            )}
          </button>

          <button
            onClick={handleJSONExport}
            disabled={!selectedFile || loading || !backendHealth}
            className="border border-blue-600 text-blue-600 hover:bg-blue-50 px-6 py-3 text-base rounded-lg font-medium disabled:border-gray-400 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center"
          >
            <FileJson className="h-5 w-5 mr-2" />
            Export as JSON
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-white rounded-lg shadow-sm border p-4 border-l-4 border-l-red-500 bg-red-50">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderResults = () => {
    if (!modernizationResults) {
      return (
        <div className="text-center py-12">
          <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Available</h3>
          <p className="text-gray-600">Please process a file first to see modernization results.</p>
        </div>
      );
    }

    const { file_info, modernized_table, mapping, data_quality, recommendations, json_export } = modernizationResults;

    return (
      <div className="space-y-8">
        {/* Success Banner */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 mr-3" />
              <div>
                <h1 className="text-2xl font-bold">Modernization Complete!</h1>
                <p className="text-green-100 mt-1">
                  Your {file_info?.detected_format?.toUpperCase()} data has been successfully transformed
                </p>
              </div>
            </div>
            {json_export && (
              <button
                onClick={() => downloadJSON(json_export, `${tableName}_complete_export.json`)}
                className="bg-white text-green-600 hover:bg-gray-100 px-4 py-2 rounded-lg font-medium flex items-center"
              >
                <FileJson className="h-5 w-5 mr-2" />
                Download JSON Export
              </button>
            )}
          </div>
        </div>

        {/* Enhanced Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <MetricCard
            icon={FileText}
            title="Records Processed"
            value={file_info?.rows_processed?.toLocaleString() || '0'}
            subtitle={`Format: ${file_info?.detected_format?.toUpperCase()}`}
            variant="primary"
          />
          <MetricCard
            icon={Database}
            title="Columns Modernized"
            value={file_info?.columns_processed || '0'}
            subtitle={file_info?.ai_processing_enabled ? 'AI Enhanced' : 'Heuristic Mode'}
            variant="success"
          />
          <MetricCard
            icon={Clock}
            title="Processing Time"
            value={`${modernizationResults.processing_time?.toFixed(2)}s` || '0s'}
            variant="warning"
          />
          <MetricCard
            icon={BarChart3}
            title="Quality Score"
            value={`${data_quality?.quality_score || 0}%`}
            variant={data_quality?.quality_score >= 90 ? 'success' : data_quality?.quality_score >= 70 ? 'warning' : 'error'}
          />
        </div>

        {/* Data Preview */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">Modernized Data Preview</h2>
          {modernized_table && modernized_table.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {Object.keys(modernized_table[0]).map((header) => (
                      <th key={header} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {modernized_table.slice(0, 10).map((row, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      {Object.values(row).map((value, cellIndex) => (
                        <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className="font-mono text-xs">{String(value)}</span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {modernized_table.length > 10 && (
                <p className="text-sm text-gray-500 mt-3 text-center">
                  Showing first 10 of {modernized_table.length} records
                </p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </div>

        {/* Column Mappings */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">AI Header Transformations</h2>
          <div className="space-y-3">
            {mapping && Object.entries(mapping).map(([original, modern]) => (
              <div key={original} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center space-x-4 flex-1">
                  <span className="font-mono text-sm text-red-600 bg-red-50 px-2 py-1 rounded">
                    {original}
                  </span>
                  <span className="text-gray-400">→</span>
                  <span className="font-mono text-sm text-green-600 bg-green-50 px-2 py-1 rounded">
                    {modern}
                  </span>
                </div>
                <StatusBadge status={original !== modern ? 'success' : 'info'}>
                  {original !== modern ? 'Improved' : 'Unchanged'}
                </StatusBadge>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Data Quality Recommendations</h2>
            <div className="space-y-4">
              {recommendations.map((rec, index) => {
                const icons = {
                  success: CheckCircle,
                  warning: AlertTriangle,
                  info: Info,
                  error: XCircle
                };
                const Icon = icons[rec.type];
                
                return (
                  <div key={index} className={`flex items-start space-x-3 p-4 rounded-lg border ${
                    rec.type === 'success' ? 'bg-green-50 border-green-200' :
                    rec.type === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                    rec.type === 'info' ? 'bg-blue-50 border-blue-200' :
                    'bg-red-50 border-red-200'
                  }`}>
                    <Icon className={`h-5 w-5 mt-0.5 ${
                      rec.type === 'success' ? 'text-green-500' :
                      rec.type === 'warning' ? 'text-yellow-500' :
                      rec.type === 'info' ? 'text-blue-500' :
                      'text-red-500'
                    }`} />
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{rec.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{rec.message}</p>
                      {rec.action && (
                        <p className="text-sm text-blue-600 mt-2 font-medium">{rec.action}</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCodeArtifacts = () => {
    if (!modernizationResults) {
      return (
        <div className="text-center py-12">
          <Code className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Code Artifacts</h3>
          <p className="text-gray-600">Process a file first to generate code artifacts.</p>
        </div>
      );
    }

    const { sql_schema, rest_api_code, docker_config } = modernizationResults;

    const artifacts = [
      {
        title: 'SQL Schema',
        content: sql_schema,
        filename: `${tableName}_schema.sql`,
        language: 'sql',
        icon: Database,
        color: 'primary'
      },
      {
        title: 'REST API',
        content: rest_api_code,
        filename: `${tableName}_api.py`,
        language: 'python',
        icon: Globe,
        color: 'success'
      },
      {
        title: 'Dockerfile',
        content: docker_config?.dockerfile,
        filename: 'Dockerfile',
        language: 'dockerfile',
        icon: Layers,
        color: 'warning'
      }
    ].filter(artifact => artifact.content); // Only show artifacts that have content

    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900">Generated Code Artifacts</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {artifacts.map((artifact, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border p-6 h-full flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <artifact.icon className={`h-5 w-5 ${
                    artifact.color === 'primary' ? 'text-blue-500' :
                    artifact.color === 'success' ? 'text-green-500' :
                    'text-yellow-500'
                  }`} />
                  <h2 className="text-lg font-semibold">{artifact.title}</h2>
                </div>
                <button
                  onClick={() => downloadFile(artifact.content, artifact.filename)}
                  className={`px-3 py-1 text-xs font-medium rounded border ${
                    artifact.color === 'primary' ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700' :
                    artifact.color === 'success' ? 'bg-green-600 text-white border-green-600 hover:bg-green-700' :
                    'bg-yellow-600 text-white border-yellow-600 hover:bg-yellow-700'
                  } flex items-center`}
                >
                  <Download className="h-3 w-3 mr-1" />
                  Download
                </button>
              </div>
              
              <div className="flex-1 min-h-0">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg h-64 text-xs overflow-auto whitespace-pre-wrap">
                  <code>{artifact.content?.substring(0, 2000)}{artifact.content?.length > 2000 ? '...' : ''}</code>
                </pre>
              </div>
            </div>
          ))}
        </div>

        {artifacts.length === 0 && (
          <div className="text-center py-12">
            <Code className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Code Artifacts Generated</h3>
            <p className="text-gray-600">The processed data did not generate code artifacts.</p>
          </div>
        )}

        {/* JSON Export Section */}
        {modernizationResults.json_export && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <FileJson className="h-5 w-5 text-purple-500" />
                <h2 className="text-lg font-semibold">Complete JSON Export</h2>
              </div>
              <button
                onClick={() => downloadJSON(modernizationResults.json_export, `${tableName}_complete_export.json`)}
                className="border border-gray-300 text-gray-700 hover:bg-gray-50 px-3 py-1 text-xs font-medium rounded flex items-center"
              >
                <Download className="h-3 w-3 mr-1" />
                Download JSON
              </button>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Complete JSON export includes:</p>
              <ul className="text-sm space-y-1 text-gray-700">
                <li>• Complete dataset with modernized column names</li>
                <li>• Comprehensive metadata and processing information</li>
                <li>• Schema definitions with data types and constraints</li>
                <li>• Column transformation mappings</li>
                <li>• Data quality statistics and recommendations</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderAnalysis = () => {
    if (!modernizationResults) {
      return (
        <div className="text-center py-12">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Available</h3>
          <p className="text-gray-600">Process a file first to see data quality analysis.</p>
        </div>
      );
    }

    const { data_quality, column_statistics } = modernizationResults;

    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900">Data Quality Analysis</h1>

        {/* Quality Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <MetricCard
            icon={BarChart3}
            title="Quality Score"
            value={`${data_quality?.quality_score || 0}%`}
            variant={data_quality?.quality_score >= 90 ? 'success' : data_quality?.quality_score >= 70 ? 'warning' : 'error'}
          />
          <MetricCard
            icon={Database}
            title="Total Records"
            value={data_quality?.total_rows?.toLocaleString() || '0'}
            variant="primary"
          />
          <MetricCard
            icon={AlertTriangle}
            title="Missing Values"
            value={data_quality?.missing_values ? Object.values(data_quality.missing_values).reduce((a, b) => a + b, 0).toLocaleString() : '0'}
            variant="warning"
          />
          <MetricCard
            icon={HardDrive}
            title="Memory Usage"
            value={formatBytes(data_quality?.memory_usage)}
            variant="error"
          />
        </div>

        {/* Column Analysis */}
        {column_statistics && Object.keys(column_statistics).length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Column Analysis</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Column</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unique Values</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Missing %</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quality</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.values(column_statistics).map((col, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className="font-mono text-sm font-medium">{col.name}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status="info">{col.dtype}</StatusBadge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{col.unique_count?.toLocaleString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{col.null_percentage?.toFixed(1)}%</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge 
                          status={
                            col.null_percentage < 5 ? 'success' : 
                            col.null_percentage < 20 ? 'warning' : 'error'
                          }
                        >
                          {col.null_percentage < 5 ? 'Excellent' : 
                           col.null_percentage < 20 ? 'Good' : 'Poor'}
                        </StatusBadge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Data Distribution Insights */}
        {column_statistics && Object.keys(column_statistics).length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Data Distribution Insights</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Data Type Distribution</h3>
                <div className="space-y-2">
                  {Object.entries(Object.values(column_statistics).reduce((acc, col) => {
                    const type = col.dtype.includes('int') ? 'Integer' : 
                                col.dtype.includes('float') ? 'Float' : 
                                col.dtype.includes('datetime') ? 'DateTime' : 'String';
                    acc[type] = (acc[type] || 0) + 1;
                    return acc;
                  }, {})).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{type}</span>
                      <StatusBadge status="info">{count} columns</StatusBadge>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Quality Distribution</h3>
                <div className="space-y-2">
                  {['Excellent', 'Good', 'Poor'].map(quality => {
                    const count = Object.values(column_statistics).filter(col => {
                      const nullPct = col.null_percentage;
                      return quality === 'Excellent' ? nullPct < 5 :
                             quality === 'Good' ? nullPct >= 5 && nullPct < 20 :
                             nullPct >= 20;
                    }).length;
                    
                    return (
                      <div key={quality} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm font-medium">{quality} Quality</span>
                        <StatusBadge status={
                          quality === 'Excellent' ? 'success' :
                          quality === 'Good' ? 'warning' : 'error'
                        }>
                          {count} columns
                        </StatusBadge>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Navigation tabs
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Monitor },
    { id: 'upload', label: 'Upload & Transform', icon: Upload },
    { id: 'results', label: 'Results', icon: CheckCircle },
    { id: 'analysis', label: 'Analysis', icon: BarChart3 },
    { id: 'artifacts', label: 'Code Artifacts', icon: Code },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Cpu className="h-8 w-8 text-blue-600 mr-3" />
              <span className="text-xl font-bold text-gray-900">AS/400 Modernizer</span>
            </div>
            <div className="flex items-center space-x-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="hidden sm:inline">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white bg-opacity-95 rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
            <div className="flex items-center space-x-4">
              <LoadingSpinner size={32} />
              <div>
                <p className="font-medium text-gray-900">Processing...</p>
                <p className="text-sm text-gray-600">
                  {selectedFile ? `Processing ${selectedFile.name}...` : 'AI is analyzing your data...'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'upload' && renderUpload()}
        {activeTab === 'results' && renderResults()}
        {activeTab === 'analysis' && renderAnalysis()}
        {activeTab === 'artifacts' && renderCodeArtifacts()}
      </main>
    </div>
  );
}

export default App;