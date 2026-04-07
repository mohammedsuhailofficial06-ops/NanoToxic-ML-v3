import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

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
  // --- Input State ---
  String material = 'Gold';
  double size = 50.0;
  double zeta = 0.0;
  double dosage = 50.0;
  
  // --- Output State ---
  String status = "Ready for Assessment";
  String prediction = "--";
  String confidence = "0%";
  String svRatio = "N/A";
  String expertAdvice = "Please input parameters to start analysis.";
  bool isLoading = false;

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
          svRatio = data['descriptors']['sv_ratio'].toString();
          status = "Analysis Complete";
          
          // --- Expert Advice Logic ---
          if (prediction == "Toxic") {
            if (zeta.abs() > 30) {
              expertAdvice = "⚠️ High surface charge detected. Suggesting Citrate capping to stabilize the particle.";
            } else if (size < 20) {
              expertAdvice = "⚠️ Ultra-small size increases cellular penetration. Suggesting PEGylation to reduce toxicity.";
            } else {
              expertAdvice = "⚠️ Toxicity likely concentration-dependent. Review dosage levels for the next assay.";
            }
          } else {
            expertAdvice = "✅ Physicochemical profile suggests low biological interference. Proceed with standard protocols.";
          }
        });
      }
    } catch (e) {
      setState(() => status = "Connection Failed: Server is currently waking up...");
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("NanoToxic-ML 3.0 | Research Portal"), centerTitle: true),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            _buildInputCard(),
            const SizedBox(height: 20),
            _buildResultCard(),
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
            const Text("Physicochemical Parameters", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            DropdownButtonFormField<String>(
              value: material,
              items: ['Gold', 'Silver', 'ZincOxide', 'Silica', 'IronOxide']
                  .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                  .toList(),
              onChanged: (v) => setState(() => material = v!),
            ),
            const SizedBox(height: 10),
            Text("Particle Size: ${size.round()} nm"),
            Slider(value: size, min: 1, max: 200, onChanged: (v) => setState(() => size = v)),
            Text("Zeta Potential: ${zeta.round()} mV"),
            Slider(value: zeta, min: -100, max: 100, onChanged: (v) => setState(() => zeta = v)),
            Text("Dosage: ${dosage.round()} ug/mL"),
            Slider(value: dosage, min: 0, max: 500, onChanged: (v) => setState(() => dosage = v)),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: isLoading ? null : runInference,
              icon: const Icon(Icons.science),
              label: Text(isLoading ? "Analyzing..." : "Run AI Assessment"),
              style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    return Card(
      color: prediction == "Toxic" ? Colors.red.withOpacity(0.1) : Colors.green.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Text(status, style: const TextStyle(fontStyle: FontStyle.italic)),
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
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(8)),
              child: Text(expertAdvice, textAlign: TextAlign.center),
            ),
          ],
        ),
      ),
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