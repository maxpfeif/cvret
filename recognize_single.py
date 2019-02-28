from PIL import Image
import pytesseract
import argparse
import cv2
import os
import csv 
import re

# timebase, based on the frame rate, so 10FPS yields 10ms timebase 
timebase = 10 

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-d", "--directory", required=True,
	help="path to directory of captured images")

args = vars(ap.parse_args())

# get the list of images 
captures = os.listdir(args["directory"])

# filter out any non-png files 
for capture in captures: 
	if not capture.endswith('.png'):
		captures.remove(capture)

captures.sort()		


# construct the data structure 
extracted_data = []


# Define config parameters.
# '-l eng'  for using the English language
# '--oem 1' for using LSTM OCR Engine
config = ('-l eng --oem 3 --psm 3')


# text recognition 
def recognize_text(image_path):
	# loading the image and converting it to grayscale 
	image = cv2.imread(image_path)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	gray = cv2.threshold(gray, 0, 255,
		cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

	#cv2.imshow("gray", gray)
	#cv2.waitKey(25)

	# write the grayscale image to disk as a temporary file so we can
	# apply OCR to it
	# tmpfilename = "{}.png".format(os.getpid())	
	tmpfilename = "TEMP.png"
	cv2.imwrite(tmpfilename, gray)
	
	# load the image as a PIL/Pillow image, apply OCR, and then delete
	# the temporary file
	text = pytesseract.image_to_string(Image.open(tmpfilename), config=config)
	os.remove(tmpfilename)
 
	# print(text)

	return text 


# extract the data text for each target parameter from the raw text 
def extract_text(raw_text):
	# there will never be "," in the data, only "."
	clean_text = raw_text.replace(",",".")

	# remove any non-numerals, periods or dashes 
	return filter_non_numerals(clean_text)


# ENSURE THAT EACH TIME THIS LOOKS AT A PARAM IT APPENDS A VALUE 
# process each image and fill the extracted data structure 
def populate_data():
	for capture in captures:
		# display the status of the conversion 
		status = "Processing " + str(captures.index(capture)) + " of " +str(len(captures))
		print (status, end="\r")
		
		# make sure we are only processing .png images 
		if capture.endswith('.png'):
			# decode the text from each capture 
			decoded_text = recognize_text(args["directory"] + "/" + capture)

			# get the data from the decoded text for each target parameter and append it  			
			extracted_data.append(extract_text(decoded_text))
	return 


# saves the detected data to a .csv file 
def save_data():
	outfile_name = "exported"
	# savefile matches the parameter name 
	output = open(outfile_name + ".csv", "w+")
	output_writer = csv.writer(output, delimiter = ",")

	time_step = 0

	for entry in extracted_data:
		output_writer.writerow([time_step*timebase,entry])
		
		time_step+=1 

	output.close()
	return 


# filters out any weird mis-identicied characters from the data 
def filter_non_numerals(unfiltered_data): 
	non_decimal = re.compile(r'[^\d.-]+')
	return non_decimal.sub('',unfiltered_data)


def main():
	populate_data()
	save_data()


#######################################################
if __name__ == "__main__":
	main()
