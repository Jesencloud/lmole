use jwalk::WalkDir;
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap};
use std::env;
use std::path::PathBuf;
use std::time::Instant;

#[derive(Serialize, Deserialize)]
struct ScanResult {
    path: String,
    total_size_bytes: u64,
    file_count: u64,
    top_files: Vec<FileInfo>,
    subdirs: HashMap<String, u64>,
}

#[derive(Serialize, Deserialize, Clone, Eq, PartialEq)]
struct FileInfo {
    path: String,
    size_bytes: u64,
}

// Implement custom ordering to make BinaryHeap a Min-Heap for size_bytes
impl Ord for FileInfo {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse order: smaller size has higher priority (will be popped first)
        other.size_bytes.cmp(&self.size_bytes)
            .then_with(|| self.path.cmp(&other.path))
    }
}

impl PartialOrd for FileInfo {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: topo-core <path>");
        std::process::exit(1);
    }

    let raw_root = &args[1];
    let root_path = PathBuf::from(raw_root)
        .canonicalize()
        .unwrap_or_else(|_| PathBuf::from(raw_root));

    if !root_path.exists() {
        eprintln!("Error: Path does not exist");
        std::process::exit(1);
    }

    let start_time = Instant::now();
    let mut total_size = 0u64;
    let mut file_count = 0u64;
    
    // Use a Min-Heap to track the top 100 largest files efficiently
    let mut top_files_heap: BinaryHeap<FileInfo> = BinaryHeap::with_capacity(101);
    let mut subdir_sizes: HashMap<String, u64> = HashMap::new();

    // Safety list - skip virtual and system-reserved directories
    let skip_list = ["proc", "sys", "dev", "run", "mnt", "media", "lost+found"];

    let walker = WalkDir::new(&root_path)
        .skip_hidden(false)
        .follow_links(false)
        .process_read_dir(move |_depth, _path, _read_dir_state, children| {
            children.retain(|child| {
                if let Ok(entry) = child {
                    let name = entry.file_name.to_string_lossy();
                    !skip_list.iter().any(|&s| name == s)
                } else {
                    false
                }
            });
        });

    for entry in walker.into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        
        if entry.file_type.is_file() {
            let size = entry.metadata().map(|m| m.len()).unwrap_or(0);
            if size > 0 {
                total_size += size;
                file_count += 1;

                // 1. Attribute size to top-level subdirectory
                if let Ok(rel_path) = path.strip_prefix(&root_path) {
                    if let Some(first_comp) = rel_path.components().next() {
                        let subdir_name = first_comp.as_os_str().to_string_lossy().into_owned();
                        *subdir_sizes.entry(subdir_name).or_insert(0) += size;
                    }
                }

                // 2. Track top 100 files (> 1MB)
                if size > 1_000_000 {
                    let info = FileInfo {
                        path: path.to_string_lossy().into_owned(),
                        size_bytes: size,
                    };
                    
                    top_files_heap.push(info);
                    if top_files_heap.len() > 100 {
                        top_files_heap.pop();
                    }
                }
            }
        }
    }

    // Convert heap to sorted vector (Largest first)
    let mut top_files: Vec<FileInfo> = top_files_heap.into_sorted_vec();
    top_files.reverse();

    let result = ScanResult {
        path: root_path.to_string_lossy().into_owned(),
        total_size_bytes: total_size,
        file_count,
        top_files,
        subdirs: subdir_sizes,
    };

    if let Ok(json) = serde_json::to_string(&result) {
        println!("{}", json);
    }
    
    eprintln!("Scan of {:?} completed in {:?}", root_path, start_time.elapsed());
}
