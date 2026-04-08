import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:file_picker/file_picker.dart'; // Rule 1: Imports at the top!

void main() => runApp(const NanoToxicApp());

class NanoToxicApp extends StatelessWidget {
  const NanoToxicApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal, brightness: Brightness.dark),
        ),
        home: const NanoPortal(),
      );
}

class NanoPortal extends StatefulWidget {
  const NanoPortal({super.key});
  @override
  State<NanoPortal> createState() => _NanoPortalState();
}

class _NanoPortalState extends State<NanoPortal> {
  // --- State Variables ---
  String material = 'Gold';
  double size = 50.0;
  double zeta = 0.0;
  double dosage = 50.0;
  String status = "Ready for Assessment";
  String prediction = "--";
  String confidence = "0%";
  String svRatio = "N/A";
  String expertAdvice = "Please input parameters to start analysis.";
  bool isLoading = false;
  List batchResults = [];

  // --- Individual Prediction ---
  Future<void> runInference() async {
    setState(() => isLoading = true);
    try {
      final response = await http.post(
        Uri.parse('https://nanotoxic-api-suhail.onrender.com/predict'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'core_material': material,
          'size_nm': size,
          'zeta_potential_mv': zeta,
          'dosage_ug_ml': dosage,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          prediction = data['prediction'];
          confidence = data['confidence'];
          svRatio = data['descriptors']['sv_ratio'].toStringAsFixed(4);
          status = "Analysis Complete";
          
          if (prediction == "Toxic") {
            expertAdvice = size < 20 
                ? "⚠️ Ultra-small size. Suggesting PEGylation." 
                : "⚠️ High toxicity. Review dosage.";
          } else {
            expertAdvice = "✅ Profile suggests low biological interference.";
          }
        });
      }
    } catch (e) {
      setState(() => status = "Connection Failed: Server waking up...");
    } finally {
      setState(() => isLoading = false);
    }
  }

  // --- Rule 2: Batch Prediction is now INSIDE the class ---
  Future<void> uploadCSV() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv'],
    );

    if (result != null) {
      setState(() {
        isLoading = true;
        status = "Processing Batch Data...";
      });
      
      try {
        var request = http.MultipartRequest(
          'POST', 
          Uri.parse('https://nanotoxic-api-suhail.onrender.com/predict_batch')
        );
        
        request.files.add(http.MultipartFile.fromBytes(
          'file', 
          result.files.first.bytes!, 
          filename: result.files.first.name
        ));

        var streamedResponse = await request.send();
        var response = await http.Response.fromStream(streamedResponse);

        if (response.statusCode == 200) {
          setState(() {
            batchResults = jsonDecode(response.body);
            status = "Batch Analysis Complete (${batchResults.length} Particles)";
          });
        }
      } catch (e) {
        setState(() => status = "Batch Upload Failed.");
      } finally {
        setState(() => isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("NanoToxic-ML 4.0 | Research Portal"), centerTitle: true),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            _buildInputCard(),
            const SizedBox(height: 10),
            TextButton.icon(
              onPressed: isLoading ? null : uploadCSV,
              icon: const Icon(Icons.upload_file),
              label: const Text("Upload Research CSV (Batch Mode)"),
            ),
            const SizedBox(height: 20),
            _buildResultCard(),
            if (batchResults.isNotEmpty) _buildBatchTable(),
          ],
        ),
      ),
    );
  }

  Widget _buildInputCard() {
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Text("Parameters", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            DropdownButtonFormField<String>(
              value: material,
              items: ['Gold', 'Silver', 'ZincOxide', 'Silica', 'IronOxide']
                  .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                  .toList(),
              onChanged: (v) => setState(() => material = v!),
            ),
            Slider(value: size, min: 1, max: 200, onChanged: (v) => setState(() => size = v)),
            Text("Size: ${size.round()} nm"),
            Slider(value: zeta, min: -100, max: 100, onChanged: (v) => setState(() => zeta = v)),
            Text("Zeta: ${zeta.round()} mV"),
            Slider(value: dosage, min: 0, max: 500, onChanged: (v) => setState(() => dosage = v)),
            Text("Dosage: ${dosage.round()} ug/mL"),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: isLoading ? null : runInference,
              child: Text(isLoading ? "Analyzing..." : "Run AI Assessment"),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    return Card(
      // Fixed: Using color values instead of deprecated opacity for v4.0
      color: prediction == "Toxic" 
          ? Colors.red.withValues(alpha: 0.1) 
          : Colors.green.withValues(alpha: 0.1),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Text(status, style: const TextStyle(color: Colors.tealAccent)),
            const Divider(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _statLabel("RESULT", prediction),
                _statLabel("CONFIDENCE", confidence),
                _statLabel("S/V RATIO", svRatio),
              ],
            ),
            const SizedBox(height: 20),
            Text(expertAdvice, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _buildBatchTable() {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: batchResults.length,
      itemBuilder: (context, index) {
        final item = batchResults[index];
        return ListTile(
          title: Text("${item['core_material']} (${item['size_nm']}nm)"),
          trailing: Text(item['prediction'], style: TextStyle(
            color: item['prediction'] == "Toxic" ? Colors.red : Colors.green,
            fontWeight: FontWeight.bold
          )),
        );
      },
    );
  }

  Widget _statLabel(String title, String value) {
    return Column(
      children: [
        Text(title, style: const TextStyle(fontSize: 10, color: Colors.grey)),
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      ],
    );
  }
}