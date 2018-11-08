#include <H5Cpp.h>
#include <iostream>
#include <fmt/format.h>
#include <map>
#include <chrono>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/mman.h>
#include <omp.h>
#include <fcntl.h>

using namespace std;
using namespace H5;

map<string, DataSet> dataSets;
vector<float> cache;
int dimensions;
int width, height, depth, stokes;
unsigned char* filePtr;

float calculateMean(vector<float>& data) {
	int N = data.size();
	float total = 0;
	int dataCount = 0;
	for (auto i = 0; i < N; i++) {
		if (!isnan(cache[i])) {
			total += cache[i];
			dataCount++;
		}
	}
	return dataCount > 0 ? total / dataCount : NAN;
}

size_t getFilesize(const char* filename) {
	struct stat st;
	stat(filename, &st);
	return st.st_size;
}

void printResult(float val) {
	fmt::print("Result: {:.2f}; ", val);
}

unsigned char* mapFile(string filename) {
	size_t filesize = getFilesize(filename.c_str());
	int fd = open(filename.c_str(), O_RDONLY, 0);
	if (fd == -1) {
		return nullptr;
	}
	return (unsigned char*) mmap(nullptr, filesize, PROT_READ, MAP_PRIVATE, fd, 0);
}

void unmapFile(string filename, void* ptr) {
	size_t filesize = getFilesize(filename.c_str());
	munmap(ptr, filesize);
}

void trialXY() {
	// XY-Image reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int z = ((float) rand()) / RAND_MAX * depth;
	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {1, height, width};
	vector<hsize_t> start = {z, 0, 0};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {height, width};
	DataSpace memspace(2, memDims);
	cache.resize(width * height);
	auto sliceDataSpace = dataSets["main"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["main"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtXY = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran XY-Image trial (z={}) in {:.2f} ms\n", z, dtXY * 1.0e-3);
}

void trialXYMmap() {
// XY-Image reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int z = ((float) rand()) / RAND_MAX * depth;
	auto sliceSizeBytes = width * height * sizeof(float);
	auto offset = dataSets["main"].getOffset() + z * sliceSizeBytes;
	cache.resize(width * height);
	memcpy(cache.data(), filePtr + offset, sliceSizeBytes);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtXY = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran XY-Image trial (z={}) in {:.2f} ms\n", z, dtXY * 1.0e-3);
}

void trialYZ() {
	// YZ-Image reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int x = ((float) rand()) / RAND_MAX * width;
	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {depth, height, 1};
	vector<hsize_t> start = {0, 0, x};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {depth, height};
	DataSpace memspace(2, memDims);
	cache.resize(depth * height);
	auto sliceDataSpace = dataSets["main"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["main"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtYZ = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran YZ-Image trial (x={}) in {:.2f} ms\n", x, dtYZ * 1.0e-3);
}

void trialYZSwizzled() {
	// YZ-Image reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int x = ((float) rand()) / RAND_MAX * width;
	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {1, height, depth};
	vector<hsize_t> start = {x, 0, 0};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {depth, height};
	DataSpace memspace(2, memDims);
	int N = depth * height;
	cache.resize(N);
	auto sliceDataSpace = dataSets["swizzled"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["swizzled"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtYZ = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran YZ-Image Swizzled trial (x={}) in {:.2f} ms.\n", x, dtYZ * 1.0e-3, mean);
}

void trialZ() {
	// Z-Profile reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int x = ((float) rand()) / RAND_MAX * width;
	int y = ((float) rand()) / RAND_MAX * height;

	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {depth, 1, 1};
	vector<hsize_t> start = {0, y, x};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {depth};
	DataSpace memspace(1, memDims);
	int N = depth;
	cache.resize(depth);
	auto sliceDataSpace = dataSets["main"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["main"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtZ = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran Z-Profile trial ({},{}) in {:.2f} ms.\n", x, y, dtZ * 1.0e-3, mean);
}

void trialZMmap() {
	omp_set_num_threads(8);
	// Z-Profile reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int x = ((float) rand()) / RAND_MAX * width;
	int y = ((float) rand()) / RAND_MAX * height;

	auto sliceSizeBytes = width * height * sizeof(float);
	auto dataSetOffset = dataSets["main"].getOffset();
	auto pixelOffset = (y * width + x) * sizeof(float);
	cache.resize(depth);

#pragma omp parallel for
	for (auto i = 0; i < depth; i++) {
		auto planeOffset = dataSetOffset + i * sliceSizeBytes;
		auto offset = planeOffset + pixelOffset;
		memcpy(cache.data() + i, filePtr + offset, sizeof(float));
	}
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtZ = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran Z-Profile trial ({},{}) in {:.2f} ms.\n", x, y, dtZ * 1.0e-3, mean);
}

void trialZSwizzled() {
	// Z-Profile reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int x = ((float) rand()) / RAND_MAX * width;
	int y = ((float) rand()) / RAND_MAX * height;

	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {1, 1, depth};
	vector<hsize_t> start = {x, y, 0};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {depth};
	DataSpace memspace(1, memDims);
	int N = depth;
	cache.resize(N);
	auto sliceDataSpace = dataSets["swizzled"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["swizzled"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtZ = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran Z-Profile Swizzled trial ({},{}) in {:.2f} ms.\n", x, y, dtZ * 1.0e-3, mean);
}

void trialRegion(int size) {
	// Z-Profile reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int x = ((float) rand()) / RAND_MAX * width;
	int y = ((float) rand()) / RAND_MAX * height;
	x = min(x, width - size - 1);
	y = min(y, height - size - 1);
	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {depth, size, size};
	vector<hsize_t> start = {0, y, x};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {depth, size, size};
	DataSpace memspace(3, memDims);
	int N = depth * size * size;
	cache.resize(N);
	auto sliceDataSpace = dataSets["main"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["main"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtZ = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran {}x{}x{} Region trial ({},{}) in {:.2f} ms.\n", size, size, depth, x, y, dtZ * 1.0e-3, mean);
}

void trialRegionSwizzled(int size) {
	// Z-Profile reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int x = ((float) rand()) / RAND_MAX * width;
	int y = ((float) rand()) / RAND_MAX * height;
	x = min(x, width - size - 1);
	y = min(y, height - size - 1);
	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {size, size, depth};
	vector<hsize_t> start = {x, y, 0};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {size, size, depth};
	DataSpace memspace(3, memDims);
	int N = depth * size * size;
	cache.resize(N);
	auto sliceDataSpace = dataSets["swizzled"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["swizzled"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtZ = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran {}x{}x{} Region Swizzled trial ({},{}) in {:.2f} ms.\n", size, size, depth, x, y, dtZ * 1.0e-3, mean);
}

void trialDownSample(int mip, bool meanFilter) {
	// XY-Image reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int z = ((float) rand()) / RAND_MAX * depth;
	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {1, height, width};
	vector<hsize_t> start = {z, 0, 0};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {height, width};
	DataSpace memspace(2, memDims);
	cache.resize(width * height);
	auto sliceDataSpace = dataSets["main"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["main"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);

	size_t numRowsRegion = height / mip;
	size_t rowLengthRegion = width / mip;
	vector<float> regionData;
	regionData.resize(numRowsRegion * rowLengthRegion);

	if (meanFilter) {
		// Perform down-sampling by calculating the mean for each MIPxMIP block
		for (auto j = 0; j < numRowsRegion; j++) {
			for (auto i = 0; i < rowLengthRegion; i++) {
				float pixelSum = 0;
				int pixelCount = 0;
				for (auto pixelX = 0; pixelX < mip; pixelX++) {
					for (auto pixelY = 0; pixelY < mip; pixelY++) {
						auto imageRow = j * mip + pixelY;
						auto imageCol = i * mip + pixelX;
						float pixVal = cache[imageRow * width + imageCol];
						if (!isnan(pixVal)) {
							pixelCount++;
							pixelSum += pixVal;
						}
					}
				}
				regionData[j * rowLengthRegion + i] = pixelCount ? pixelSum / pixelCount : NAN;
			}
		}
	} else {
		// Nearest neighbour filtering
		for (auto j = 0; j < numRowsRegion; j++) {
			for (auto i = 0; i < rowLengthRegion; i++) {
				auto imageRow = j * mip;
				auto imageCol = i * mip;
				regionData[j * rowLengthRegion + i] = cache[imageRow * width + imageCol];
			}
		}
	}

	float dsMean = calculateMean(regionData);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtXY = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(dsMean);
	fmt::print("Ran XY Down-sample x{} {} trial (z={}) in {:.2f} ms\n", mip, meanFilter ? "(mean)" : "(nn)", z, dtXY * 1.0e-3);
}

void trialReadMip(int mip) {
	// XY-Image reads
	auto tStart = std::chrono::high_resolution_clock::now();
	int z = ((float) rand()) / RAND_MAX * depth;
	size_t numRowsRegion = height / mip;
	size_t rowLengthRegion = width / mip;
	// Define dimensions of hyperslab in 2D
	vector<hsize_t> count = {1, numRowsRegion, rowLengthRegion};
	vector<hsize_t> start = {z, 0, 0};

	// Append channel (and stokes in 4D) to hyperslab dims
	if (dimensions == 4) {
		count.insert(count.begin(), {1});
		start.insert(start.begin(), {0});
	}

	// Read data into memory space
	hsize_t memDims[] = {numRowsRegion, rowLengthRegion};
	DataSpace memspace(2, memDims);
	cache.resize(rowLengthRegion * numRowsRegion);
	auto sliceDataSpace = dataSets["main"].getSpace();
	sliceDataSpace.selectHyperslab(H5S_SELECT_SET, count.data(), start.data());
	dataSets["main"].read(cache.data(), PredType::NATIVE_FLOAT, memspace, sliceDataSpace);
	float mean = calculateMean(cache);
	auto tEnd = std::chrono::high_resolution_clock::now();
	auto dtXY = std::chrono::duration_cast<std::chrono::microseconds>(tEnd - tStart).count();
	printResult(mean);
	fmt::print("Ran XY MIP Read x{} trial (z={}) in {:.2f} ms\n", mip, z, dtXY * 1.0e-3);
}

int main(int argc, char* argv[]) {

	int mipLevel = 8;

	// string filename = "/home/angus/cubes_hdf5/DEEP_2_I_cube.hdf5";
	string filename = "/home/angus/cubes_hdf5/GALFACTS_N4_0263_4023_10chanavg_I.hdf5";
	auto file = H5File(filename, H5F_ACC_RDONLY);
	auto hduGroup = file.openGroup("0");
	dataSets["main"] = hduGroup.openDataSet("DATA");
	auto& dataSet = dataSets["main"];

	vector<hsize_t> dims(dataSet.getSpace().getSimpleExtentNdims(), 0);
	dataSet.getSpace().getSimpleExtentDims(dims.data(), nullptr);
	dimensions = dims.size();
	width = dims[dimensions - 1];
	height = dims[dimensions - 2];
	depth = (dimensions > 2) ? dims[dimensions - 3] : 1;
	stokes = (dimensions > 3) ? dims[dimensions - 4] : 1;

	if (dimensions == 3) {
		dataSets["swizzled"] = hduGroup.openDataSet("SwizzledData/ZYX");
	} else {
		dataSets["swizzled"] = hduGroup.openDataSet("SwizzledData/ZYXW");
	}

	srand(time(nullptr));

	if (argc != 2) {
		return 1;
	}

	int val = atoi(argv[1]);

	// Memory map for trials that require it
	if (val >= 13) {
		filePtr = mapFile(filename);
	}

	switch (val) {
		case 0: trialXY();
			break;
		case 1: trialYZ();
			break;
		case 2: trialYZSwizzled();
			break;
		case 3: trialZ();
			break;
		case 4: trialZSwizzled();
			break;
		case 5: trialRegion(32);
			break;
		case 6: trialRegionSwizzled(32);
			break;
		case 7: trialRegion(64);
			break;
		case 8: trialRegionSwizzled(64);
			break;
		case 9: trialRegion(128);
			break;
		case 10: trialRegionSwizzled(128);
			break;
		case 11: trialDownSample(mipLevel, true);
			break;
		case 12: trialReadMip(mipLevel);
			break;
		case 13: trialXYMmap();
			break;
		case 14: trialZMmap();
			break;
		default:break;
	}

	if (val >= 13) {
		unmapFile(filename, filePtr);
	}

	file.close();
	return 0;
}